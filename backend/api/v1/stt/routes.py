from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .schemas import Speech_Synthesis
from .services import transcribe_audio
from database import get_db

router = APIRouter(prefix="/synthesize", tags=["STT"])

@router.get("/")
@router.get("/health")
def health():
    return {"status": "Synthesis running !"}

@router.post("/")
def transcribe(request: Speech_Synthesis, db: Session = Depends(get_db)):
    video_id = request.video_id
    response = transcribe_audio(video_id, db)

    return response
