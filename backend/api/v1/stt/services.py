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
    file_path = video_row.audio_path
    print(file_path)

    if not os.path.exists(file_path):
        return {
            'location' : 'TRANSCRIPTION',
            'error': "FILE NOT FOUND !!"
        }
    
    try:
        print("\n\nTranscription Started !!\n\n")
        start_time = time.time()
        
        segments, info = model.transcribe(file_path, beam_size=5) # get transcription text segments
        
        result = []
        for segment in segments: # list of dictionaries, containing timestamps and text for each segment
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
            print("refersh")
        except SQLAlchemyError as e:
            db.rollback()
            return {
                'location' : 'STT-SERVICES',
                'error'    : str(e)
            }
        finally:
            db.close()

        print("\n\n Time Taken: ", end_time-start_time)
        print("\n\n")

        return { # return detected language, probablity of correct language detection, and the segments
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