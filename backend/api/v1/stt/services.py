from faster_whisper import WhisperModel
from .models import Transcripts
from ..videos.models import Videos
from sqlalchemy.exc import SQLAlchemyError
import os, time, json

try:
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
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
            "text": existing.original_transcript
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
        
        # Whisper processes the mono file found in your stored audio_path
        segments, info = model.transcribe(mono_file, beam_size=5) 
        
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
                src_lang = info.language,
                original_transcript = json.dumps(result)
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
            'language'            : info.language,
            'language_probablity' : info.language_probability,
            'segments'            : result
        }
    except Exception as e:
        return {
            'location': "TRANSCRIPTION",
            'error'   : str(e)
        }


def transcribe_background():
    pass