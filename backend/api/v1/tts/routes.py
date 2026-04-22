from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .schemas import TextToSpeechRequest
from .services import seperate_dialogues_background
from database import get_db

router = APIRouter(prefix="/text_to_speech", tags=['TTS'])

@router.get("/health")
def health():
    return {
        "status": "success"
    }

@router.get("/")
def text_to_speech(request: TextToSpeechRequest, db:Session = Depends(get_db)):
    try:
        data = request.model_dump()
        video_id = data.get("video_id")

        seperate_dialogues_background(video_id, db)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }