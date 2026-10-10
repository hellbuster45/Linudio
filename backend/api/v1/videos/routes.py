import asyncio
from fastapi import APIRouter, BackgroundTasks, Depends
from .services import get_video
from ..helpers import get_metadata
from .schemas import YoutubeVideo
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/videos", tags=["Video Management"])

@router.get("/")
@router.get("/health")
def health():
    return {"status": "Running !"}

# download from youtube
# Return immediate reponse with VIDEO_ID & video metadata
# Start downloading in background
@router.post("/yt_video")
async def get_yt_video(video_data: YoutubeVideo, bg_task: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        # yt-dlp is blocking; keep it off the event loop
        metadata = await asyncio.to_thread(get_metadata, video_data.url)

        if "error" in metadata:
            return metadata

        bg_task.add_task(get_video, video_data.url, db, metadata)

        return {
            "message": "Download Started..",
            "metadata": metadata
        }
    except Exception as e:
        return {
            'location' : 'VIDEOS_ROUTES',
            'error'    : str(e)
        }
