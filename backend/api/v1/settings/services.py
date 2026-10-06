import torch
from core.config import settings
from ..stt import services as stt_services
from ..text_translation import services as translation_services

VALID_DEVICES = {"cpu", "cuda", "auto"}
VALID_WHISPER_MODELS = {"tiny", "small", "medium", "large-v3", "large-v3-turbo"}
VALID_NLLB_MODELS = {
    "facebook/nllb-200-distilled-600M",
    "facebook/nllb-200-distilled-1.3B",
    "facebook/nllb-200-3.3B",
}

def get_device_info():
    return {
        "device": settings.DEVICE,
        "active_stt_device": stt_services.current_device,
        "active_translation_device": str(translation_services.device) if translation_services.device else None,
        "cuda_available": torch.cuda.is_available(),
        "whisper_model": stt_services.current_model_size,
        "nllb_model": translation_services.current_model_name,
    }

def _resolve_device(requested_device: str):
    if requested_device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return requested_device

def set_device(requested_device: str):
    if requested_device not in VALID_DEVICES:
        return {
            "location": "SETTINGS",
            "error": f"Invalid device '{requested_device}'. Must be one of {sorted(VALID_DEVICES)}"
        }

    if requested_device == "cuda" and not torch.cuda.is_available():
        return {
            "location": "SETTINGS",
            "error": "CUDA requested but no CUDA-capable GPU is available on this machine."
        }

    resolved = _resolve_device(requested_device)
    settings.DEVICE = requested_device

    try:
        # Preserve whatever model sizes are already active; only the device changes.
        stt_services.load_model(resolved, stt_services.current_model_size)
        translation_services.load_model(resolved, translation_services.current_model_name)
    except Exception as e:
        return {
            "location": "SETTINGS",
            "error": f"Failed to reload models on device '{resolved}': {str(e)}"
        }

    return get_device_info()

def set_whisper_model(model_size: str):
    if model_size not in VALID_WHISPER_MODELS:
        return {
            "location": "SETTINGS",
            "error": f"Invalid Whisper model '{model_size}'. Must be one of {sorted(VALID_WHISPER_MODELS)}"
        }

    settings.WHISPER_MODEL = model_size
    resolved_device = _resolve_device(settings.DEVICE)

    try:
        stt_services.load_model(resolved_device, model_size)
    except Exception as e:
        return {
            "location": "SETTINGS",
            "error": f"Failed to load Whisper model '{model_size}': {str(e)}"
        }

    return get_device_info()

def set_nllb_model(model_name: str):
    if model_name not in VALID_NLLB_MODELS:
        return {
            "location": "SETTINGS",
            "error": f"Invalid NLLB model '{model_name}'. Must be one of {sorted(VALID_NLLB_MODELS)}"
        }

    settings.NLLB_MODEL = model_name
    resolved_device = _resolve_device(settings.DEVICE)

    try:
        translation_services.load_model(resolved_device, model_name)
    except Exception as e:
        return {
            "location": "SETTINGS",
            "error": f"Failed to load NLLB model '{model_name}': {str(e)}"
        }

    return get_device_info()
