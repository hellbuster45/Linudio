from fastapi import APIRouter, BackgroundTasks
from .services import yt_downloader, get_metadata

router = APIRouter(prefix="/videos", tags=["Video Management"])

# download from youtube
# Return immediate reponse with video metadata
# Start downloading in background
@router.post("/")
def get_video(url: str):
    metadata = get_metadata(url)

    BackgroundTasks.add_task(yt_downloader, url)
    return {
        "message": "Download Started..",
        "metadata": metadata
    }
