from fastapi import APIRouter, BackgroundTasks, Depends
from .services import get_transcript
from ..helpers import get_metadata
from .schemas import YoutubeVideo
from sqlalchemy.orm import Session
from . import models
from database import get_db
import os
from ..speech_synthesis.services import transcribe_audio

router = APIRouter(prefix="/videos", tags=["Video Management"])

@router.get("/")
@router.get("/health")
def health():
    return {"status": "Running !"}

# download from youtube
# Return immediate reponse with video metadata
# Start downloading in background
@router.post("/yt_video")
def get_video(request: YoutubeVideo, bg_task: BackgroundTasks, db: Session=Depends(get_db)):
    metadata = get_metadata(request.url)

    bg_task.add_task(get_transcript, db, request.url)
    return {
        "message": "Download Started..",
        "metadata": metadata
    }

@router.get("/transcript/{video_id}")
def get_transcript_status(video_id: str, db: Session=Depends(get_db)): # endpoint for client polling, to check if the transcript processing has been done
    transcript_obj = db.query(models.Transcripts).filter_by(video_id=video_id).first()
    
    if transcript_obj.status == "pending":
        try:
            file_path = f"storage\\audio\\{video_id}.wav"
            if os.path.exists(file_path):
                try: # Begin Transcription for the respective audio file
                    transcript = transcribe_audio(file_path)
                except Exception as e:
                    return {"error": f"TRANSCRIPTION ERROR: {str(e)}"}
                
                try: # update transcript row with the new text, and commit to Database.
                    transcript_obj.transcript = transcript["result"]
                    transcript_obj.status = "success"
                    db.commit()
                except Exception as e:
                    db.rollback()
                    return {"error": f"DATABASE UPDATION ERROR: {str(e)}"}
                
        except Exception as e:
            return {"error": str(e)}
        
        return {
            "status": str(transcript_obj.status),
            "transcript": str(transcript_obj.transcript)
        }
    else:
        return {"status": "processing"}