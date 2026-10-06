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

        text_segments = []
        if data.get('segments'):
            print("Text present in request body")
            text_segments = data.get('segments')
        else:
            print("Text NOT present in request body")
            row = db.query(Transcripts).filter(Transcripts.video_id == video_id).first()
            text_segments = row.original_transcript
            # print(text_segments)

        tgt_lang = None
        print("TGT_LANG: ", data.get("tgt_lang"))
        if 'tgt_lang' in data:
            tgt_lang = data.get("tgt_lang")

        # text = json.loads(data['text'])
        start_time = time.time()
        translated = await translate_text(video_id, db, text_segments, tgt_lang)
        end_time = time.time()

        print(f"TIME TAKEN: {end_time - start_time}")
        return translated
    except Exception as e:
        return {
            "location": "TEXT_TRANSLATION",
            "error": str(e)
        }