from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from database import get_db
from .services import translate_text
import json

router = APIRouter(prefix="/translate", tags=["Translate"])


@router.post("/")
async def translate(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    video_id = data["video_id"]
    text = json.loads(data['text'])
    translated = await translate_text(video_id, text, db)
    return translated
