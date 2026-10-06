from .models import Transcripts
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from sqlalchemy.exc import SQLAlchemyError
from core.config import resolve_device, settings
from .models import Transcripts
import torch, json

model = None
tokenizer = None
device = None
current_model_name = None

def load_model(target_device: str = None, model_name: str = None):
    """Loads (or reloads) the NLLB model + matching tokenizer onto the given device. Updates module globals."""
    global model, tokenizer, device, current_model_name

    target_device = target_device or resolve_device()
    model_name = model_name or settings.NLLB_MODEL
    device = torch.device(target_device)
    model_dtype = torch.float16 if device.type == "cuda" else torch.float32

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=model_dtype)
    model = model.to(device)
    current_model_name = model_name
    return model

load_model()

async def translate_text(video_id: str, db, text: list=None, tgt_lang: str="hin_Deva"):
    try:
        text_input = [] # Array of strings from text transcript dict
        for items in text:
            text_input.append(items.get('text'))
        
        inputs = tokenizer(
            text_input,
            return_tensors = "pt",
            padding = True,
            truncation = True,
            max_length = 512
        ).to(device)

        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate Translation
        print("Starting Translation...")
        with torch.no_grad():
            translated_tokens = model.generate (
                **inputs,
                forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang),
                max_length = 512,
                num_beams = 4,
                early_stopping = True
            )

        translated_texts = tokenizer.batch_decode (
            translated_tokens,
            skip_special_tokens = True
        )

        # Format result
        translated_result = None
        if len(translated_texts) == 1 and not isinstance(text, list):
            translated_result = translated_texts[0]
        else:
            translated_result = translated_texts

        for i, item in enumerate(text):
            item['text'] = translated_result[i]

        row = db.query(Transcripts).filter(Transcripts.video_id == video_id).first()
        row.tgt_lang = tgt_lang
        row.translated_transcript = text
        db.add(row)
        db.commit()
        db.refresh(row)

        return {
            "status": "success",
            "tgt_lang": tgt_lang,
            "translated_segments": text
        }
    except SQLAlchemyError as e:
        return {
            "status": "sql_error",
            "location": "TRANSLATION_SERVICE",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "location": "TRANSLATION_SERVICE",
            "error": str(e)
        }