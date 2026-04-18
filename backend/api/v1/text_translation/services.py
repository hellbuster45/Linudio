from .models import Transcripts
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

model_name = "facebook/nllb-200-distilled-600M"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

device = torch.device("cpu")
model = model.to(device)

async def translate_text(video_id: str, db, text: list=None, src_lang="eng_Latn", tgt_lang="fra_Latn"):
    try:
        text_input = [item['text'] for item in text] # Array of strings from text transcript dict

        inputs = tokenizer(
            text_input,
            return_tensors = "pt",
            padding = True,
            truncation = True,
            max_length = 512
        ).to(device)

        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Generate Translation
        with torch.no_grad():
            translated_tokens = model.generate(
                **inputs,
                forced_bos_token_id = tokenizer.convert_tokens_to_ids(tgt_lang),
                max_length = 512,
                num_beams = 4,
                early_stopping = True
            )
        
        translated_texts = tokenizer.batch_decode(
            translated_tokens,
            skip_special_tokens = True
        )

        # Format result
        translated_result = None
        if len(translated_texts) == 1 and not isinstance(text, list):
            translated_result = translated_texts[0]
        else:
            translated_result = translated_texts

        return {
            "message": "success",
            "translated_text": translated_result
        }
    except Exception as e:
        return {
            "status": "error",
            "location": "TRANSLATION_SERVICE",
            "error": str(e)
        }