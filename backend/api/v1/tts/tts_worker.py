import sys
import os
import json
import time
import gc
import tempfile
import traceback
from pathlib import Path

# This file runs as a standalone script, so make the backend's own packages (core.*) importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from core.progress import install_download_progress_hook, set_progress_sink
from melo.api import TTS

# A short phrase per language, spoken once while preparing a voice. Some of MeloTTS' text models
# only download when they are first used, so merely loading the voice isn't enough to cache it.
SAMPLE_TEXT = {
    "EN": "Welcome to the dubbed video.",
    "ES": "Bienvenido al video doblado.",
    "FR": "Bienvenue dans la vidéo doublée.",
    "ZH": "欢迎观看配音视频。",
    "JP": "吹き替え動画へようこそ。",
    "KR": "더빙된 영상에 오신 것을 환영합니다.",
}

_model_cache = {}  # (lang, device) -> TTS instance, so a single warm process can serve multiple languages/devices

def get_model(lang, device):
    key = (lang, device)
    if key not in _model_cache:
        print(f"[WORKER] Loading MeloTTS model for {lang} on {device}...", file=sys.stderr)
        _model_cache[key] = TTS(language=lang, device=device)
    return _model_cache[key]

def run_batch(batch_file, lang, output_dir, device="cpu"):
    model = get_model(lang, device)
    speaker_ids = model.hps.data.spk2id
    default_spk_id = list(speaker_ids.values())[0]

    with open(batch_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)

    print(f"[WORKER] Starting generation for {len(segments)} segments...", file=sys.stderr)
    for seg in segments:
        text = seg['text']
        seg_id = seg['id']
        output_path = os.path.join(output_dir, f"seg_{seg_id}.wav")

        # quiet=True is required: MeloTTS otherwise prints sentence-split debug info to
        # stdout, which would corrupt the JSON-line protocol used in serve() mode.
        model.tts_to_file(text, default_spk_id, output_path, speed=1.0, quiet=True)
        print(f"[WORKER] Generated segment {seg_id}", file=sys.stderr)

def emit(event: dict):
    """Sends a progress event to the server. Events share stdout with the final result line
    (told apart by the "event" key), so nothing else may print to stdout."""
    print(json.dumps(event), flush=True)

def prepare_voices(langs, device="cpu"):
    """Downloads and warms up the given voices one at a time (each is released again straight
    away, so preparing all six doesn't need all six in memory)."""
    install_download_progress_hook()
    last_sent = [0.0]

    def forward_progress(downloaded, total):
        now = time.monotonic()
        if now - last_sent[0] >= 0.25 or (total and downloaded >= total):
            last_sent[0] = now
            emit({"event": "progress", "downloaded": downloaded, "total": total})

    set_progress_sink(forward_progress)
    try:
        for lang in langs:
            emit({"event": "voice", "lang": lang})
            model = TTS(language=lang, device=device)
            speaker = list(model.hps.data.spk2id.values())[0]
            with tempfile.TemporaryDirectory() as tmp:
                model.tts_to_file(SAMPLE_TEXT[lang], speaker, os.path.join(tmp, "warmup.wav"), speed=1.0, quiet=True)
            del model
            gc.collect()
    finally:
        set_progress_sink(None)

def run_batch_tts(batch_file, lang, output_dir, device="cpu"):
    """One-shot entry point, kept for standalone/manual invocation."""
    try:
        run_batch(batch_file, lang, output_dir, device)
        return 0
    except Exception:
        print(f"[WORKER] Error:\n{traceback.format_exc()}", file=sys.stderr)
        return 1

def serve():
    """
    Persistent worker mode: reads one JSON job per line from stdin, writes one JSON
    result per line to stdout. Keeps the process (and its loaded models) alive across jobs,
    avoiding the ~20s torch/melo import cost on every single dub job.

    Job:    {"batch_file": str, "lang": str, "output_dir": str, "device": str}
            or {"op": "prepare", "langs": [str, ...], "device": str}
    Events: {"event": "voice", "lang": str} and {"event": "progress", "downloaded": int, "total": int|null}
            (only while preparing voices), each on its own line before the result.
    Result: {"status": "ok"} or {"status": "error", "message": str}
    """
    print("[WORKER] Ready, waiting for jobs on stdin...", file=sys.stderr)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line == "__shutdown__":
            print("[WORKER] Shutdown requested, exiting.", file=sys.stderr)
            break

        try:
            job = json.loads(line)
            if job.get("op") == "prepare":
                prepare_voices(job["langs"], job.get("device", "cpu"))
            else:
                run_batch(job["batch_file"], job["lang"], job["output_dir"], job.get("device", "cpu"))
            result = {"status": "ok"}
        except Exception:
            result = {"status": "error", "message": traceback.format_exc()}

        print(json.dumps(result), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        serve()
    elif len(sys.argv) >= 4:
        device_arg = sys.argv[4] if len(sys.argv) > 4 else "cpu"
        exit_code = run_batch_tts(sys.argv[1], sys.argv[2], sys.argv[3], device_arg)
        sys.exit(exit_code)
    else:
        sys.exit(1)
