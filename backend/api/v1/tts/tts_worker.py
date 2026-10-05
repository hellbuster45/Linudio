import sys
import os
import json
import traceback
from melo.api import TTS

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
