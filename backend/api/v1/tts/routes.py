from fastapi import APIRouter, BackgroundTasks, HTTPException
from .schemas import TextToSpeechRequest
from .services import process_dubbing
import os

router = APIRouter(prefix="/text_to_speech", tags=['TTS'])

@router.get("/health")
def health():
    return {
        "status": "success"
    }

@router.get("/dub")
async def text_to_speech(request: TextToSpeechRequest, background_tasks: BackgroundTasks):
    
    # Quick validation: check if the original video exists before starting
    video_path = f"storage/{request.video_id}/{request.video_id}_video.mp4"
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Original video not found in storage")
    
    # Add the long-running task to the background
    # This calls the 'process_dubbing' method in your services.py
    background_tasks.add_task(
        process_dubbing, 
        request.video_id, 
        request.segments, 
        request.lang_code
    )

    return {
        "status": "Started..",
        "video_id": request.video_id
    }