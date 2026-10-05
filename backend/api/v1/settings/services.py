import torch
from core.config import settings
from ..stt import services as stt_services
from ..text_translation import services as translation_services

VALID_DEVICES = {"cpu", "cuda", "auto"}

def get_device_info():
    return {
        "device": settings.DEVICE,
        "active_stt_device": stt_services.current_device,
        "active_translation_device": str(translation_services.device) if translation_services.device else None,
        "cuda_available": torch.cuda.is_available(),
    }

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

    resolved = requested_device
    if requested_device == "auto":
        resolved = "cuda" if torch.cuda.is_available() else "cpu"

    settings.DEVICE = requested_device

    try:
        stt_services.load_model(resolved)
        translation_services.load_model(resolved)
    except Exception as e:
        return {
            "location": "SETTINGS",
            "error": f"Failed to reload models on device '{resolved}': {str(e)}"
        }

    return get_device_info()
