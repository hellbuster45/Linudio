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
        print(data)
        video_id = data["video_id"]

        text = []
        if 'text' in data:
            print("Text present in request body")
            text = data.get('text')
        else:
            print("Text NOT present in request body")
            row = db.query(Transcripts).filter(Transcripts.video_id == video_id).first()
            text = row.original_transcript
            print(text)
        
        tgt_lang = None
        print("TGT_LANG: ", data.get("tgt_lang"))
        if 'tgt_lang' in data:
            tgt_lang = data.get("tgt_lang")
        
        # text = json.loads(data['text'])
        start_time = time.time()
        translated = await translate_text(video_id, db, text, tgt_lang)
        end_time = time.time()
        
        print(f"TIME TAKEN: {end_time - start_time}")
        return translated
    except Exception as e:
        return {
            "location": "TEXT_TRANSLATION",
            "error": str(e)
        }