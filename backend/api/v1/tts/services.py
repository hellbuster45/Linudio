import os, sys, asyncio, shutil, traceback, time, json
from sqlalchemy.exc import SQLAlchemyError
from core.config import settings
from .models import DubStatus

NLLB_TO_MELO = {
    "eng_Latn": "EN", "spa_Latn": "ES", "fra_Latn": "FR",
    "zho_Hans": "ZH", "jpn_Jpan": "JP", "kor_Hang": "KR"
}

STORAGE_ROOT = "storage/videos"

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
    _worker_process = await asyncio.create_subprocess_exec(
        "python", worker_path, "--serve",
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
        job_row.status = progress_state
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise e

async def process_dubbing(video_id: str, segments: list, nllb_lang_code: str, db):
    job_row = db.query(DubStatus).filter(DubStatus.video_id == video_id, DubStatus.status == "pending").first()
    if job_row:
        start_total = time.time()
        print(f"\n--- [START] Processing Dubbing: {video_id} ---")
        
        try:
            video_dir = os.path.join(STORAGE_ROOT, video_id)
            temp_dir = os.path.join(video_dir, "temp_dubs")

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir, exist_ok=True)
            
            update_status(video_id, 'seperation', db)

            # 1. AUDIO SEPARATION
            print(f"\n[STEP 1/3] AUDIO SEPARATION")
            bgm_path = await separate_audio(video_id, video_dir)
            if not bgm_path or not os.path.exists(bgm_path):
                print(f"[CRITICAL] Separation failed.")
                return

            update_status(video_id, 'tts_generation', db)

            # 2. EFFICIENT BATCH TTS GENERATION
            print(f"\n[STEP 2/3] BATCH TTS GENERATION")
            melo_lang = NLLB_TO_MELO.get(nllb_lang_code, "EN")
            
            batch_data = [{"id": s.id, "text": s.text} for s in segments]
            batch_file = os.path.join(temp_dir, "batch_segments.json")
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(batch_data, f, ensure_ascii=False)

            tts_ok = await run_tts_job(batch_file, melo_lang, temp_dir, settings.DEVICE)

            if tts_ok:
                print("[DEBUG] Batch TTS successful. Starting individual duration syncs...")
                for seg in segments:
                    seg_path = os.path.join(temp_dir, f"seg_{seg.id}.wav")
                    if os.path.exists(seg_path):
                        target_dur = seg.end_time - seg.start_time
                        # This modifies the file on disk, keeping the object-id link intact
                        await sync_duration(seg_path, target_dur)
            else:
                print(f"[ERROR] Batch TTS failed")
                return

            # 3. FINAL MIX & MUX
            print(f"\n[STEP 3/3] FINAL ASSEMBLY")
            
            # CRITICAL FIX: Pass 'segments' (the list of objects), 
            # NOT 'dubbed_files' (which was a list of strings).
            await assemble_final_output(video_id, segments, bgm_path, video_dir)
            
            print(f"\n--- [FINISH] Total Time: {time.time() - start_total:.2f}s ---")
            
            update_status(video_id, 'complete', db)
        except Exception:
            print(f"\n[CRITICAL ERROR] Pipeline Crashed:\n{traceback.format_exc()}")

async def sync_duration(path, target_dur):
    """Calculates drift and applies atempo filter if needed."""
    probe = f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{path}"'
    proc = await asyncio.create_subprocess_shell(probe, stdout=asyncio.subprocess.PIPE)
    stdout, _ = await proc.communicate()
    
    try:
        actual_dur = float(stdout.decode().strip() or 0)
        if actual_dur > 0:
            speed = actual_dur / target_dur
            if 0.5 <= speed <= 2.0 and abs(1 - speed) > 0.05:
                sync_path = path.replace(".wav", "_sync.wav")
                # No more pass—we execute and check
                rc = await run_shell_cmd(["ffmpeg", "-y", "-i", path, "-filter:a", f"atempo={speed}", sync_path], "FFmpeg-Sync")
                if rc == 0:
                    os.replace(sync_path, path)
    except Exception as e:
        print(f"    [WARN] sync_duration failed: {str(e)}")

async def separate_audio(video_id, video_dir):
    input_audio = os.path.join(video_dir, f"{video_id}_stereo.wav")
    
    # We add --normalization 0.9 to prevent audio clipping during separation
    sep_cmd = [
        "audio-separator", input_audio,
        "--model_filename", "Kim_Vocal_2.onnx",
        "--output_dir", video_dir,
        "--output_format", "WAV",
        "--normalization", "0.9" 
    ]
    
    print(f"[DEBUG] Running Audio-Separator on {input_audio}...")
    rc = await run_shell_cmd(sep_cmd, "Audio-Separator")
    
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
        # Optional: Rename it to a consistent name for easier debugging later
        standard_bgm = os.path.join(video_dir, f"{video_id}_bgm_final.wav")
        os.replace(bgm_file, standard_bgm)
        return standard_bgm
    
    print("[ERROR] Could not locate the separated background file in the directory.")
    return None

async def assemble_final_output(video_id: str, segments: list, bgm_path: str, video_dir: str):
    video_dir = os.path.abspath(video_dir)
    voice_only = os.path.join(video_dir, "translated_vocals.wav")
    mixed_audio = os.path.join(video_dir, "final_mix.wav")
    original_video = os.path.join(video_dir, f"{video_id}_video.mp4")
    final_output = os.path.join(video_dir, f"{video_id}_dubbed.mp4")
    temp_dir = os.path.abspath(os.path.join(video_dir, "temp_dubs"))

    input_args = []
    filter_parts = []
    input_count = 0
    
    # 1. BUILD INPUTS AND FILTERS
    for seg in segments:
        seg_path = os.path.join(temp_dir, f"seg_{seg.id}.wav")
        
        if os.path.exists(seg_path):
            delay_ms = int(seg.start_time * 1000)
            # Use absolute paths and ensure they are ready for shell
            input_args.extend(["-i", f'"{seg_path}"'])
            filter_parts.append(f"[{input_count}:a]volume=2.5,adelay={delay_ms}|{delay_ms}[v{input_count}];")
            input_count += 1

    if input_count == 0:
        print("[ERROR] No segment files found in temp_dubs!")
        return

    merge_labels = "".join([f"[v{i}]" for i in range(input_count)])
    # The filter MUST be wrapped in double quotes for Windows shell
    # complex_filter = f"\"{''.join(filter_parts)}{merge_labels}amix=inputs={input_count}:dropout_transition=0[voice]\""
    complex_filter = f"\"{''.join(filter_parts)}{merge_labels}amix=inputs={input_count}:duration=longest:dropout_transition=0:normalize=0[voice]\""

    # 2. STEP A: CREATE ALIGNED VOCALS
    print(f"[ASSEMBLY] Creating merged vocals: {voice_only}")
    # We build the string manually to ensure quotes are exactly where they need to be
    # align_cmd = f"ffmpeg -y {' '.join(input_args)} -filter_complex {complex_filter} -map [voice] \"{voice_only}\""
    align_cmd = f"ffmpeg -y {' '.join(input_args)} -filter_complex {complex_filter} -map [voice] \"{voice_only}\""
    
    # Use create_subprocess_shell directly to avoid list-to-string issues
    process = await asyncio.create_subprocess_shell(
        align_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()

    # 3. STEP B: MIX WITH BGM
    if os.path.exists(voice_only):
        print(f"[ASSEMBLY] Mixing with BGM...")
        mix_filter = "\" [0:a]volume=1.2[v]; [1:a]volume=0.4[bg]; [v][bg]amix=inputs=2:duration=longest:normalize=0[out] \""
        # mix_cmd = f"ffmpeg -y -i \"{voice_only}\" -i \"{bgm_path}\" -filter_complex \"amix=inputs=2:duration=longest:dropout_transition=0\" \"{mixed_audio}\""
        mix_cmd = f"ffmpeg -y -i \"{voice_only}\" -i \"{bgm_path}\" -filter_complex {mix_filter} -map \"[out]\" \"{mixed_audio}\""
        process = await asyncio.create_subprocess_shell(mix_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()
    else:
        print(f"[ERROR] voice_only file was never created. Check FFmpeg logs.")
        return

    # 4. STEP C: MUX
    if os.path.exists(mixed_audio):
        print(f"[ASSEMBLY] Final Muxing...")
        mux_cmd = f"ffmpeg -y -i \"{original_video}\" -i \"{mixed_audio}\" -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest \"{final_output}\""
        process = await asyncio.create_subprocess_shell(mux_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

# async def assemble_final_output(video_id, files, bgm_path, video_dir):
#     # Concat list creation
#     list_path = os.path.join(video_dir, "concat_list.txt")
#     with open(list_path, "w", encoding="utf-8") as f:
#         for f_path in files:
#             f.write(f"file '{os.path.abspath(f_path)}'\n")
    
#     voice_only = os.path.join(video_dir, "translated_vocals.wav")
#     mixed_audio = os.path.join(video_dir, "final_mix.wav")
#     original_video = os.path.join(video_dir, f"{video_id}_video.mp4")
#     final_output = os.path.join(video_dir, f"{video_id}_dubbed.mp4")

#     # 1. Concat
#     await run_shell_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", voice_only], "Final-Concat")
#     # 2. Mix
#     await run_shell_cmd(["ffmpeg", "-y", "-i", voice_only, "-i", bgm_path, "-filter_complex", "amix=inputs=2:duration=first", mixed_audio], "Final-Mix")
#     # 3. Mux
#     await run_shell_cmd(["ffmpeg", "-y", "-i", original_video, "-i", mixed_audio, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-shortest", final_output], "Final-Mux")

# async def assemble_final_output(video_id, files, bgm_path, video_dir):
#     # Concat list creation
#     list_path = os.path.join(video_dir, "concat_list.txt")
#     with open(list_path, "w", encoding="utf-8") as f:
#         for f_path in files:
#             # Use forward slashes for FFmpeg list paths to avoid Windows backslash escapes
#             normalized_path = os.path.abspath(f_path).replace("\\", "/")
#             f.write(f"file '{normalized_path}'\n")
    
#     voice_only = os.path.join(video_dir, "translated_vocals.wav")
#     mixed_audio = os.path.join(video_dir, "final_mix.wav")
#     original_video = os.path.join(video_dir, f"{video_id}_video.mp4")
#     final_output = os.path.join(video_dir, f"{video_id}_dubbed.mp4")

#     # 1. Concat translated segments
#     await run_shell_cmd(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", voice_only], "Final-Concat")

#     # 2. Mix with BGM (Normalization added to keep volume levels high)
#     # amix=dropout_transition=0 prevents audio from cutting out if one stream is slightly shorter
#     await run_shell_cmd([
#         "ffmpeg", "-y", "-i", voice_only, "-i", bgm_path, 
#         "-filter_complex", "amix=inputs=2:duration=first:dropout_transition=0,volume=2", 
#         mixed_audio
#     ], "Final-Mix")

#     # 3. Mux with Video - THE FIX
#     # We MUST encode to 'aac' because .mp4 containers don't like .wav (pcm) streams
#     await run_shell_cmd([
#         "ffmpeg", "-y", 
#         "-i", original_video, 
#         "-i", mixed_audio, 
#         "-map", "0:v:0",    # Take video from original
#         "-map", "1:a:0",    # Take audio from the new mix
#         "-c:v", "copy",     # Don't re-encode video (fast)
#         "-c:a", "aac",      # Encode audio to AAC for MP4 compatibility
#         "-b:a", "192k",     # Good quality bitrate
#         "-shortest",        # End when video ends
#         final_output
#     ], "Final-Mux")

async def run_shell_cmd(cmd_list, task_name):
    """Executes shell commands and streams output to console in real-time."""
    print(f"\n[EXEC] {task_name}")
    
    formatted = [f'"{str(a)}"' if any(x in str(a) for x in [" ", "\\", "/"]) else str(a) for a in cmd_list]
    cmd_str = " ".join(formatted)
    
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    process = await asyncio.create_subprocess_shell(
        cmd_str,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env
    )

    async def stream_output(stream, prefix):
        while True:
            line = await stream.readline()
            if not line: break
            # Print output (FFmpeg/Separator). Subprocess output can contain characters
            # (e.g. progress-bar glyphs) that Windows' console encoding can't display;
            # encode/decode through the console's own encoding with replacement so a
            # single unprintable character can't crash this draining loop.
            text = line.decode(errors='replace').strip()
            safe_text = text.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace")
            print(f"      [{prefix}] {safe_text}")

    # Gather handles both streams without blocking
    await asyncio.gather(
        stream_output(process.stdout, "OUT"),
        stream_output(process.stderr, "ERR")
    )

    await process.wait()
    return process.returncode