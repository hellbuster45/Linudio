from fastapi import APIRouter, Depends
from .schemas import TranslationRequest
from sqlalchemy.orm import Session
from database import get_db
from .services import translate_text
from .models import Transcripts
import json, time

router = APIRouter(prefix="/translate", tags=["Translate"])

@router.post("/")
async def translate(request: TranslationRequest, db: Session = Depends(get_db)):
    try:
        data = request.model_dump()
        print("DATA: ", data)
        video_id = data["video_id"]

        text = []
        if data.get('text') != None:
            text = data.get("text")
        else:
            row = db.query(Transcripts).filter(Transcripts.video_id == video_id).first()
            text = row.original_transcript
            print(text)
        
        # text = json.loads(data['text'])
        start_time = time.time()
        translated = await translate_text(video_id, db, text=text)
        end_time = time.time()
        
        print(f"TIME TAKEN: {end_time - start_time}")
        return translated
    except Exception as e:
        return {
            "location": "TEXT_TRANSLATION",
            "error": str(e)
        }