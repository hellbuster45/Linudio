import os, sys, asyncio, shutil, traceback, time, json
from sqlalchemy.exc import SQLAlchemyError
from core.config import settings
from core.proc import run_command
from .models import DubStatus

NLLB_TO_MELO = {
    "eng_Latn": "EN", "spa_Latn": "ES", "fra_Latn": "FR",
    "zho_Hans": "ZH", "jpn_Jpan": "JP", "kor_Hang": "KR"
}

# --- Persistent TTS worker ---
# tts_worker.py's torch/melo import takes ~20s; spawning a fresh subprocess per dub job
# pays that cost every time. Instead we keep one long-lived worker process alive across
# jobs (started lazily, on first use) and talk to it via a JSON-line stdin/stdout protocol.
# Only one job is sent at a time (_worker_lock) since one worker process can't safely run
# two TTS generations concurrently — dubbing is already processed sequentially today anyway.
_worker_process = None
_worker_lock = asyncio.Lock()

async def _start_worker():
    global _worker_process
    worker_path = os.path.join(os.path.dirname(__file__), "tts_worker.py")
    # sys.executable (not "python") so the worker runs in the same environment as the server.
    _worker_process = await asyncio.create_subprocess_exec(
        sys.executable, worker_path, "--serve",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    asyncio.create_task(_drain_stderr(_worker_process))

async def _drain_stderr(process):
    """Continuously reads the worker's stderr so its pipe never fills up and blocks it."""
    while True:
        line = await process.stderr.readline()
        if not line:
            break
        print(f"      [TTS-WORKER] {line.decode(errors='replace').rstrip()}")

async def run_tts_job(batch_file: str, lang: str, output_dir: str, device: str) -> bool:
    """Sends one TTS job to the persistent worker, restarting it first if it's dead. Returns True on success."""
    global _worker_process

    async with _worker_lock:
        if _worker_process is None or _worker_process.returncode is not None:
            print("[TTS-WORKER] Starting persistent worker process...")
            await _start_worker()

        job = json.dumps({
            "batch_file": batch_file,
            "lang": lang,
            "output_dir": output_dir,
            "device": device,
        })

        try:
            _worker_process.stdin.write((job + "\n").encode("utf-8"))
            await _worker_process.stdin.drain()

            response_line = await _worker_process.stdout.readline()
            if not response_line:
                print("[TTS-WORKER] Worker closed its stdout unexpectedly (likely crashed).")
                return False

            result = json.loads(response_line.decode("utf-8"))
            if result.get("status") != "ok":
                print(f"[TTS-WORKER] Job failed:\n{result.get('message')}")
                return False
            return True
        except (BrokenPipeError, ConnectionResetError):
            print("[TTS-WORKER] Worker pipe broke (likely crashed). It will be restarted on the next job.")
            return False

def update_status(video_id: str, progress_state: str, db):
    try:
        job_row = db.query(DubStatus).filter(DubStatus.video_id == video_id).first()
        if job_row is None:
            return
        job_row.status = progress_state
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e

def _fail(video_id: str, db, reason: str):
    """Marks the job failed so the UI stops waiting instead of spinning forever."""
    print(f"[CRITICAL] Dubbing failed: {reason}")
    try:
        update_status(video_id, 'failed', db)
    except SQLAlchemyError:
        pass

async def process_dubbing(video_id: str, segments: list, nllb_lang_code: str, db):
    job_row = db.query(DubStatus).filter(DubStatus.video_id == video_id, DubStatus.status == "pending").first()
    if not job_row:
        return

    start_total = time.time()
    print(f"\n--- [START] Processing Dubbing: {video_id} ---")

    try:
        video_dir = str(settings.videos_dir / video_id)
        temp_dir = os.path.join(video_dir, "temp_dubs")

        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)

        update_status(video_id, 'seperation', db)

        # 1. AUDIO SEPARATION
        print(f"\n[STEP 1/3] AUDIO SEPARATION")
        bgm_path = await separate_audio(video_id, video_dir)
        if not bgm_path or not os.path.exists(bgm_path):
            return _fail(video_id, db, "Audio separation failed.")

        update_status(video_id, 'tts_generation', db)

        # 2. EFFICIENT BATCH TTS GENERATION
        print(f"\n[STEP 2/3] BATCH TTS GENERATION")
        melo_lang = NLLB_TO_MELO.get(nllb_lang_code, "EN")

        batch_data = [{"id": s.id, "text": s.text} for s in segments]
        batch_file = os.path.join(temp_dir, "batch_segments.json")
        with open(batch_file, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, ensure_ascii=False)

        tts_ok = await run_tts_job(batch_file, melo_lang, temp_dir, settings.DEVICE)
        if not tts_ok:
            return _fail(video_id, db, "Batch TTS failed.")

        print("[DEBUG] Batch TTS successful. Starting individual duration syncs...")
        for seg in segments:
            seg_path = os.path.join(temp_dir, f"seg_{seg.id}.wav")
            if os.path.exists(seg_path):
                target_dur = seg.end_time - seg.start_time
                # This modifies the file on disk, keeping the object-id link intact
                await sync_duration(seg_path, target_dur)

        # 3. FINAL MIX & MUX
        print(f"\n[STEP 3/3] FINAL ASSEMBLY")
        if not await assemble_final_output(video_id, segments, bgm_path, video_dir):
            return _fail(video_id, db, "Final assembly failed.")

        print(f"\n--- [FINISH] Total Time: {time.time() - start_total:.2f}s ---")

        update_status(video_id, 'complete', db)
    except Exception:
        print(f"\n[CRITICAL ERROR] Pipeline Crashed:\n{traceback.format_exc()}")
        _fail(video_id, db, "Unexpected error (see traceback above).")

async def sync_duration(path, target_dur):
    """Calculates drift and applies atempo filter if needed."""
    rc, stdout = await run_command(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        "FFprobe",
    )

    try:
        actual_dur = float(stdout.strip() or 0) if rc == 0 else 0
        if actual_dur > 0:
            speed = actual_dur / target_dur
            if 0.5 <= speed <= 2.0 and abs(1 - speed) > 0.05:
                sync_path = path.replace(".wav", "_sync.wav")
                rc, _ = await run_command(
                    ["ffmpeg", "-y", "-i", path, "-filter:a", f"atempo={speed}", sync_path],
                    "FFmpeg-Sync",
                )
                if rc == 0:
                    os.replace(sync_path, path)
    except Exception as e:
        print(f"    [WARN] sync_duration failed: {str(e)}")

async def separate_audio(video_id, video_dir):
    input_audio = os.path.join(video_dir, f"{video_id}_stereo.wav")

    # Run audio-separator through the current interpreter (rather than looking for an
    # "audio-separator" executable on PATH, which isn't there when running from an
    # un-activated virtualenv). --normalization 0.9 prevents clipping during separation.
    sep_cmd = [
        sys.executable, "-c", "from audio_separator.utils.cli import main; main()",
        input_audio,
        "--model_filename", "Kim_Vocal_2.onnx",
        "--output_dir", video_dir,
        "--output_format", "WAV",
        "--normalization", "0.9",
    ]

    print(f"[DEBUG] Running Audio-Separator on {input_audio}...")
    rc, _ = await run_command(sep_cmd, "Audio-Separator", stream_prefix="Audio-Separator")

    if rc != 0:
        print("[ERROR] Audio-Separator process returned a non-zero exit code.")
        return None

    # Dynamically find the background/instrumental file
    # This avoids the "Expected path missing" error when the tool changes naming conventions
    files = os.listdir(video_dir)
    bgm_file = None

    for f in files:
        # Look for the file that isn't the vocals and isn't the original
        if ("(Instrumental)" in f or "(Background)" in f) and f.endswith(".wav"):
            bgm_file = os.path.join(video_dir, f)
            break

    if bgm_file:
        print(f"[DEBUG] Found background track: {bgm_file}")
        # Rename it to a consistent name for easier debugging later
        standard_bgm = os.path.join(video_dir, f"{video_id}_bgm_final.wav")
        os.replace(bgm_file, standard_bgm)
        return standard_bgm

    print("[ERROR] Could not locate the separated background file in the directory.")
    return None

async def assemble_final_output(video_id: str, segments: list, bgm_path: str, video_dir: str) -> bool:
    video_dir = os.path.abspath(video_dir)
    voice_only = os.path.join(video_dir, "translated_vocals.wav")
    mixed_audio = os.path.join(video_dir, "final_mix.wav")
    original_video = os.path.join(video_dir, f"{video_id}_video.mp4")
    final_output = os.path.join(video_dir, f"{video_id}_dubbed.mp4")
    temp_dir = os.path.abspath(os.path.join(video_dir, "temp_dubs"))

    # Remove outputs from earlier runs so a failure can't be mistaken for success.
    for stale in (voice_only, mixed_audio, final_output):
        if os.path.exists(stale):
            os.remove(stale)

    input_args = []
    filter_parts = []
    input_count = 0

    # 1. BUILD INPUTS AND FILTERS
    for seg in segments:
        seg_path = os.path.join(temp_dir, f"seg_{seg.id}.wav")

        if os.path.exists(seg_path):
            delay_ms = int(seg.start_time * 1000)
            input_args.extend(["-i", seg_path])
            filter_parts.append(f"[{input_count}:a]volume=2.5,adelay={delay_ms}|{delay_ms}[v{input_count}];")
            input_count += 1

    if input_count == 0:
        print("[ERROR] No segment files found in temp_dubs!")
        return False

    merge_labels = "".join([f"[v{i}]" for i in range(input_count)])
    complex_filter = f"{''.join(filter_parts)}{merge_labels}amix=inputs={input_count}:duration=longest:dropout_transition=0:normalize=0[voice]"

    # 2. STEP A: CREATE ALIGNED VOCALS
    print(f"[ASSEMBLY] Creating merged vocals: {voice_only}")
    rc, _ = await run_command(
        ["ffmpeg", "-y", *input_args, "-filter_complex", complex_filter, "-map", "[voice]", voice_only],
        "FFmpeg-Align",
    )
    if rc != 0 or not os.path.exists(voice_only):
        print("[ERROR] voice_only file was never created. Check FFmpeg logs.")
        return False

    # 3. STEP B: MIX WITH BGM
    print(f"[ASSEMBLY] Mixing with BGM...")
    mix_filter = "[0:a]volume=1.2[v]; [1:a]volume=0.4[bg]; [v][bg]amix=inputs=2:duration=longest:normalize=0[out]"
    rc, _ = await run_command(
        ["ffmpeg", "-y", "-i", voice_only, "-i", bgm_path, "-filter_complex", mix_filter, "-map", "[out]", mixed_audio],
        "FFmpeg-Mix",
    )
    if rc != 0 or not os.path.exists(mixed_audio):
        print("[ERROR] Mixed audio was never created. Check FFmpeg logs.")
        return False

    # 4. STEP C: MUX
    print(f"[ASSEMBLY] Final Muxing...")
    rc, _ = await run_command(
        ["ffmpeg", "-y", "-i", original_video, "-i", mixed_audio,
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", final_output],
        "FFmpeg-Mux",
    )
    return rc == 0 and os.path.exists(final_output)
