from fastapi import APIRouter, BackgroundTasks
from .services import downloader, get_metadata
from .schemas import YoutubeVideo

router = APIRouter(prefix="/videos", tags=["Video Management"])

@router.get("/")
@router.get("/health")
def health():
    return {"status": "Running !"}

# download from youtube
# Return immediate reponse with video metadata
# Start downloading in background
@router.post("/yt_video")
def get_video(request: YoutubeVideo, bg_task: BackgroundTasks):
    metadata = get_metadata(request.url)

    bg_task.add_task(downloader, request.url)
    return {
        "message": "Download Started..",
        "metadata": metadata
    }
