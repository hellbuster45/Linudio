from .models import Transcripts
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

model_name = "facebook/nllb-200-distilled-600M"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

device = torch.device("cpu")
model = model.to(device)

async def translate_text(video_id: str, text: list, db, src_lang="eng_Latn", tgt_lang="fra_Latn"):
    inputs = tokenizer(
        text,
        return_tensors = "pt",
        padding = True,
        truncation = True,
        max_length = 512
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Generate Translation
    with torch.no_grad():
        translated_tokens = model.generate(
            **inputs,
            forced_bos_token_id = tokenizer.lang_code_to_id[tgt_lang],
            max_length = 512,
            num_beams = 4,
            early_stopping = True
        )
    
    translated_texts = tokenizer.batch_decode(
        translated_tokens,
        skip_special_tokens = True
    )

    # Format result
    if len(translated_texts) == 1 and not isinstance(text, list):
        translated_result = translated_texts[0]
    else:
        translated_result = translated_texts