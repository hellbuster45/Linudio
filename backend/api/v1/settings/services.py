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

# In-memory status of the most recent/ongoing settings change.
# Single-user, single-process app: one load happens at a time, so a
# module-level dict is enough — no need for per-job tracking.
_status = {
    "stage": "idle",  # "idle" | "loading" | "ready" | "error"
    "target": None,   # human-readable description of what's being loaded
    "error": None,
}

def get_status():
    return dict(_status)

def _set_status(stage: str, target: str = None, error: str = None):
    _status["stage"] = stage
    _status["target"] = target
    _status["error"] = error

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

def validate_device(requested_device: str):
    if requested_device not in VALID_DEVICES:
        return f"Invalid device '{requested_device}'. Must be one of {sorted(VALID_DEVICES)}"
    if requested_device == "cuda" and not torch.cuda.is_available():
        return "CUDA requested but no CUDA-capable GPU is available on this machine."
    return None

def validate_whisper_model(model_size: str):
    if model_size not in VALID_WHISPER_MODELS:
        return f"Invalid Whisper model '{model_size}'. Must be one of {sorted(VALID_WHISPER_MODELS)}"
    return None

def validate_nllb_model(model_name: str):
    if model_name not in VALID_NLLB_MODELS:
        return f"Invalid NLLB model '{model_name}'. Must be one of {sorted(VALID_NLLB_MODELS)}"
    return None

def set_device(requested_device: str):
    resolved = _resolve_device(requested_device)
    settings.DEVICE = requested_device

    try:
        _set_status("loading", target=f"Switching device to {requested_device}")
        # Preserve whatever model sizes are already active; only the device changes.
        stt_services.load_model(resolved, stt_services.current_model_size)
        translation_services.load_model(resolved, translation_services.current_model_name)
    except Exception as e:
        _set_status("error", error=f"Failed to reload models on device '{resolved}': {str(e)}")
        return

    _set_status("ready")

def set_whisper_model(model_size: str):
    settings.WHISPER_MODEL = model_size
    resolved_device = _resolve_device(settings.DEVICE)

    try:
        _set_status("loading", target=f"Transcription model: {model_size}")
        stt_services.load_model(resolved_device, model_size)
    except Exception as e:
        _set_status("error", error=f"Failed to load Whisper model '{model_size}': {str(e)}")
        return

    _set_status("ready")

def set_nllb_model(model_name: str):
    settings.NLLB_MODEL = model_name
    resolved_device = _resolve_device(settings.DEVICE)

    try:
        _set_status("loading", target=f"Translation model: {model_name}")
        translation_services.load_model(resolved_device, model_name)
    except Exception as e:
        _set_status("error", error=f"Failed to load NLLB model '{model_name}': {str(e)}")
        return

    _set_status("ready")
