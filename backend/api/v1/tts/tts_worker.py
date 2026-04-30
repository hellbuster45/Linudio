import sys
import os
import json
import traceback
from melo.api import TTS

def run_batch_tts(batch_file, lang, output_dir):
    try:
        print(f"[WORKER] Loading MeloTTS model for {lang} on CPU...")
        model = TTS(language=lang, device="cpu")
        speaker_ids = model.hps.data.spk2id
        default_spk_id = list(speaker_ids.values())[0]

        with open(batch_file, 'r', encoding='utf-8') as f:
            segments = json.load(f)

        print(f"[WORKER] Starting generation for {len(segments)} segments...")
        for seg in segments:
            text = seg['text']
            seg_id = seg['id']
            output_path = os.path.join(output_dir, f"seg_{seg_id}.wav")
            
            # Actual generation
            model.tts_to_file(text, default_spk_id, output_path, speed=1.0)
            print(f"[WORKER] Generated segment {seg_id}")

        return 0
    except Exception:
        print(f"[WORKER] Error:\n{traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit(1)
    
    exit_code = run_batch_tts(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(exit_code)