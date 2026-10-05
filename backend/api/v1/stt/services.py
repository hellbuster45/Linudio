from faster_whisper import WhisperModel, BatchedInferencePipeline
from sqlalchemy.exc import SQLAlchemyError
from core.utils import WHISPER_TO_NLLB
from core.config import resolve_device, settings
from .models import Transcripts
from ..videos.models import Videos
import os, time

model = None
batched_model = None
current_device = None

def load_model(device: str = None):
    """Loads (or reloads) the Whisper model onto the given device. Updates module globals."""
    global model, batched_model, current_device

    device = device or resolve_device()
    compute_type = "float16" if device == "cuda" else "int8"

    model = WhisperModel("large-v3-turbo", device=device, compute_type=compute_type)
    # Wrapping costs nothing until .transcribe() is actually called with batch_size > 1,
    # so we always build it and decide whether to use it per-call based on STT_BATCH_SIZE.
    batched_model = BatchedInferencePipeline(model=model)
    current_device = device
    return model

try:
    load_model()
except Exception as e:
    print({
        'location': "TRANSCRIPTION",
        'error'   : e
    })

def transcribe_audio(video_id, db):
    existing = db.query(Transcripts).filter(Transcripts.video_id == video_id).first()
    if existing:
        print("existing found")
        return {
            "src_lang": existing.src_lang,
            "language_probability": existing.probability,
            "segments": existing.original_transcript
        }
    
    video_row = db.query(Videos).filter(Videos.video_id == video_id).first()
    
    # Use the base_path stored in your audio_path column
    folder_path = video_row.audio_path 
    
    # Construct the path to the mono file inside that stored folder
    mono_file = os.path.join(folder_path, f"{video_id}_mono.wav")
    print(f"Targeting: {mono_file}")

    if not os.path.exists(mono_file):
        return {
            'location' : 'TRANSCRIPTION',
            'error': f"FILE NOT FOUND AT {mono_file}!!"
        }
    
    try:
        print("\n\nTranscription Started !!\n\n")
        start_time = time.time()

        # Whisper processes the mono file found in your stored audio_path.
        # STT_BATCH_SIZE > 1 trades higher RAM usage for faster throughput (opt-in, see core/config.py).
        # Note: BatchedInferencePipeline silently ignores no_speech_threshold/compression_ratio_threshold,
        # and defaults without_timestamps=True, so we must override it explicitly to keep segment timing.
        # Tested on a single CPU-bound file: no speed gain and measurably worse accuracy
        # (dropped/duplicated words, overlapping segments) vs the default path below.
        if settings.STT_BATCH_SIZE > 1:
            segments, info = batched_model.transcribe(
                mono_file,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                without_timestamps=False,
                batch_size=settings.STT_BATCH_SIZE
            )
        else:
            segments, info = model.transcribe(
                mono_file,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                no_speech_threshold=0.7,
                compression_ratio_threshold=2.4
            )

        result = []
        for segment in segments: 
            result.append({
                'id'         : segment.id,
                'start_time' : segment.start,
                'end_time'   : segment.end,
                'text'       : segment.text
            })
        
        end_time = time.time()

        try:
            transcript_row = Transcripts(
                video_id = video_id,
                src_lang = WHISPER_TO_NLLB.get(info.language),
                probability = info.language_probability,
                original_transcript = result
            )
            db.add(transcript_row)
            print("row made")

            db.commit()
            print("commit")
            
            db.refresh(transcript_row)
            print("refresh")
        except SQLAlchemyError as e:
            db.rollback()
            return {
                'location' : 'STT-SERVICES',
                'error'    : str(e)
            }

        print("\n\n Time Taken: ", end_time-start_time)
        print("\n\n")

        return { 
            'src_lang'            : WHISPER_TO_NLLB.get(info.language),
            'language_probability' : info.language_probability,
            'segments'            : result
        }
    except Exception as e:
        return {
            'location': "TRANSCRIPTION",
            'error'   : str(e)
        }