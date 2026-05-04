from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from .schemas import TextToSpeechRequest
from .schemas import DubStatusRequest
from .services import process_dubbing
from .models import DubStatus
import os

router = APIRouter(prefix="/text_to_speech", tags=['TTS'])

@router.get("/health")
def health():
    return {
        "status": "success"
    }

@router.post("/dub")
async def text_to_speech(request: TextToSpeechRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    
    # Quick validation: check if the original video exists before starting
    video_path = f"storage/videos/{request.video_id}/{request.video_id}_video.mp4"
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Original video not found in storage")
    
    # Add the long-running task to the background
    # This calls the 'process_dubbing' method in your services.py
    background_tasks.add_task(
        process_dubbing, 
        request.video_id, 
        request.segments, 
        request.lang_code,
        db
    )

    try:
        row = DubStatus (
            video_id = request.video_id,
            status   = 'pending'
        )
        db.add(row)
        db.commit()
        db.refresh(row)
    except SQLAlchemyError as e:
        raise e

    return {
        "status": "started",
        "video_id": request.video_id
    }

@router.get("/dub_status")
def get_dub_status(video_id: str, db: Session = Depends(get_db)):

    row = db.query(DubStatus).filter(DubStatus.video_id == video_id).first()
    print("ROW_STATUS: ", row.status)
    if(row.status == "complete"):
        path = f"storage/videos/{video_id}/{video_id}_dubbed.mp4"
        if os.path.exists(path):

            try:
                db.delete(row)
                db.commit()
            except SQLAlchemyError as e:
                raise e

            return {
                "status": "success",
                "video_path": f"http://localhost:8000/storage/{video_id}/{video_id}_dubbed.mp4"
            }
    return {
        "status": row.status
    }