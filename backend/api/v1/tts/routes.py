from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import get_db
from core.config import settings
from core.validation import VideoId
from .schemas import TextToSpeechRequest
from .services import process_dubbing
from .models import DubStatus

router = APIRouter(prefix="/text_to_speech", tags=['TTS'])

# Job states that mean "finished"; anything else means a dub is still running.
FINISHED_STATES = ("complete", "failed")

@router.get("/health")
def health():
    return {
        "status": "success"
    }

@router.post("/dub")
async def text_to_speech(request: TextToSpeechRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    # Quick validation: check if the original video exists before starting
    video_path = settings.videos_dir / request.video_id / f"{request.video_id}_video.mp4"
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Original video not found in storage")

    try:
        existing = db.query(DubStatus).filter(DubStatus.video_id == request.video_id).first()
        if existing and existing.status not in FINISHED_STATES:
            raise HTTPException(status_code=409, detail="A dub for this video is already in progress")

        # Replace any leftover row from an earlier finished/failed run with a fresh one.
        if existing:
            db.delete(existing)
        db.add(DubStatus(video_id=request.video_id, status='pending'))
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not create dubbing job: {e}")

    # Add the long-running task to the background
    background_tasks.add_task(
        process_dubbing,
        request.video_id,
        request.segments,
        request.lang_code,
        db
    )

    return {
        "status": "started",
        "video_id": request.video_id
    }

@router.get("/dub_status")
def get_dub_status(video_id: VideoId, db: Session = Depends(get_db)):

    row = db.query(DubStatus).filter(DubStatus.video_id == video_id).first()
    if row is None:
        return {"status": "not_found"}

    if row.status == "complete":
        path = settings.videos_dir / video_id / f"{video_id}_dubbed.mp4"
        if path.exists():
            try:
                db.delete(row)
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                raise e

            # Relative to the API server; the frontend adds its own API base URL.
            return {
                "status": "success",
                "video_path": f"/storage/{video_id}/{video_id}_dubbed.mp4"
            }

    if row.status == "failed":
        # Report the failure once, then clear the job so the video can be dubbed again.
        db.delete(row)
        db.commit()
        return {"status": "failed"}

    return {
        "status": row.status
    }
