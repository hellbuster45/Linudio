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
        
        metadata = get_metadata(video_data.url)

        bg_task.add_task(get_video, video_data.url, db, metadata)
        
        return {
            "message": "Download Started..",
            "metadata": metadata
        }
    except Exception as e:
        raise e
        # return {
        #     'location' : 'ROUTES',
        #     'error'    : str(e)
        # }
