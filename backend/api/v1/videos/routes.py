from fastapi import APIRouter, BackgroundTasks, Depends
from .services import get_or_create_transcript, get_metadata
from .schemas import YoutubeVideo
from sqlalchemy.orm import Session
from . import models
from database import get_db

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

    bg_task.add_task(get_or_create_transcript, db, request.url)
    return {
        "message": "Download Started..",
        "metadata": metadata
    }

@router.get("/transcript/{video_id}")
def get_transcript_status(video_id: str, db: Session=Depends(get_db)): # endpoint for client polling, to check if the transcript processing has been done
    transcript_obj = db.query(models.Transcripts).filter_by(video_id=video_id).first()
    if transcript_obj.status == "pending":
        return {"status": str(transcript_obj.status)}
    elif transcript_obj.status == "success":
        return {
            "status": str(transcript_obj.status),
            "transcript": transcript_obj.transcript
        }
    else:
        return {"status": "processing"}