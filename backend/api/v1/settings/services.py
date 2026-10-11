import asyncio
import os
import subprocess
import sys

import torch
from core.config import settings
from core.preflight import NLTK_RESOURCES, english_speech_data_ready, japanese_dictionary_ready, korean_tokenizer_ready
from core.progress import (
    status as _status,
    set_status as _set_status,
    set_download_progress,
    install_download_progress_hook,
)
from ..stt import services as stt_services
from ..text_translation import services as translation_services
from ..tts import services as tts_services

VALID_DEVICES = {"cpu", "cuda", "auto"}
VALID_WHISPER_MODELS = {"tiny", "small", "medium", "large-v3", "large-v3-turbo"}
VALID_NLLB_MODELS = {
    "facebook/nllb-200-distilled-600M",
    "facebook/nllb-200-distilled-1.3B",
    "facebook/nllb-200-3.3B",
}

# Voices are offered in this order (MeloTTS language codes).
VALID_VOICES = list(tts_services.VOICE_LABELS)

# Set once the whole first-time setup has finished. Nothing auto-loads on startup, so the
# frontend uses is_ready() to decide between showing the setup flow and the app.
_setup_complete = False

def get_status():
    return dict(_status)

def is_ready() -> bool:
    """True once first-time setup has finished and both models are loaded."""
    return _setup_complete and stt_services.model is not None and translation_services.model is not None

def get_device_info():
    return {
        "device": settings.DEVICE,
        "active_stt_device": stt_services.current_device,
        "active_translation_device": str(translation_services.device) if translation_services.device else None,
        "cuda_available": torch.cuda.is_available(),
        "whisper_model": stt_services.current_model_size,
        "nllb_model": translation_services.current_model_name,
        # Pre-selected in the Set Up panel before anything is loaded (from .env / last choice).
        "default_whisper_model": settings.WHISPER_MODEL,
        "default_nllb_model": settings.NLLB_MODEL,
        "is_ready": is_ready(),
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

def validate_setup(device: str, whisper_model: str, nllb_model: str, voices: list[str] | None = None):
    unknown = [v for v in (voices or []) if v not in VALID_VOICES]
    return (
        validate_device(device)
        or validate_whisper_model(whisper_model)
        or validate_nllb_model(nllb_model)
        or (f"Unknown voice(s) {unknown}. Must be from {VALID_VOICES}" if unknown else None)
    )

def resolve_voices(requested: list[str] | None, korean_available: bool) -> list[str]:
    """The voices to prepare: the requested ones (all of them by default), in the standard order.
    Korean is left out when its tokenizer is not installed, since it could only fail."""
    wanted = VALID_VOICES if requested is None else [v for v in VALID_VOICES if v in requested]
    return [v for v in wanted if v != "KR" or korean_available]

def plan_setup_steps(whisper_model: str, nllb_model: str, voices: list[str],
                     dictionary_missing: bool, english_data_missing: bool) -> list[tuple[str, str]]:
    """The ordered (key, label) steps of first-time setup. The dictionary and language data come
    first because loading any voice needs them."""
    steps: list[tuple[str, str]] = []
    if dictionary_missing:
        steps.append(("dictionary", "Japanese dictionary (about 0.8 GB)"))
    if english_data_missing and "EN" in voices:
        steps.append(("english_data", "English language data"))
    steps.append(("whisper", f"Transcription model: {whisper_model}"))
    steps.append(("nllb", f"Translation model: {nllb_model}"))
    steps.append(("separator", "Voice separation model"))
    for voice in voices:
        steps.append((f"voice:{voice}", f"Voice: {tts_services.VOICE_LABELS[voice]}"))
    return steps

def _download_unidic() -> None:
    result = subprocess.run([sys.executable, "-m", "unidic", "download"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if result.returncode != 0:
        raise RuntimeError(f"Could not download the Japanese dictionary: {(result.stderr or result.stdout)[-500:]}")

def _download_english_data() -> None:
    import nltk
    for resource in NLTK_RESOURCES:
        if not nltk.download(resource, download_dir=os.environ.get("NLTK_DATA"), quiet=True):
            raise RuntimeError(f"Could not download the English language data ({resource}).")

async def setup_models(device: str, whisper_model: str, nllb_model: str, voices: list[str] | None = None):
    """First-time setup, all in one go: the dictionary and language data MeloTTS needs, both AI
    models, the voice separation model and the dubbing voices. Everything is downloaded and
    checked now, so the first real job does not stall on hidden downloads."""
    global _setup_complete
    _setup_complete = False
    install_download_progress_hook()
    settings.DEVICE = device
    settings.WHISPER_MODEL = whisper_model
    settings.NLLB_MODEL = nllb_model
    resolved = _resolve_device(device)

    voices = resolve_voices(voices, korean_tokenizer_ready())
    steps = plan_setup_steps(
        whisper_model, nllb_model, voices,
        dictionary_missing=not japanese_dictionary_ready(),
        english_data_missing=not english_speech_data_ready(),
    )
    step_number = {key: i + 1 for i, (key, _) in enumerate(steps)}
    label = dict(steps)

    def begin(key: str):
        _set_status("loading", target=label[key], step=step_number[key], total_steps=len(steps))

    def on_worker_event(event: dict):
        if event["event"] == "voice":
            begin(f"voice:{event['lang']}")
        elif event["event"] == "progress":
            set_download_progress(event["downloaded"], event["total"])

    try:
        for key, _ in steps:
            if key.startswith("voice:"):
                continue  # handled together below, in a single pass through the TTS worker
            begin(key)
            if key == "dictionary":
                await asyncio.to_thread(_download_unidic)
            elif key == "english_data":
                await asyncio.to_thread(_download_english_data)
            elif key == "whisper":
                await asyncio.to_thread(stt_services.load_model, resolved, whisper_model)
            elif key == "nllb":
                await asyncio.to_thread(translation_services.load_model, resolved, nllb_model)
            elif key == "separator":
                await asyncio.to_thread(tts_services.download_separator_model)

        if voices:
            begin(f"voice:{voices[0]}")
            ok, error = await tts_services.prepare_voices(voices, resolved, on_worker_event)
            if not ok:
                _set_status("error", error=f"Failed to prepare the dubbing voices: {error}")
                return
    except Exception as e:
        _set_status("error", error=f"Failed to set up: {str(e)}")
        return

    _setup_complete = True
    _set_status("ready")

def set_device(requested_device: str):
    if not is_ready():
        _set_status("error", error="Models haven't been set up yet. Complete initial setup first.")
        return

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
    if not is_ready():
        _set_status("error", error="Models haven't been set up yet. Complete initial setup first.")
        return

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
    if not is_ready():
        _set_status("error", error="Models haven't been set up yet. Complete initial setup first.")
        return

    settings.NLLB_MODEL = model_name
    resolved_device = _resolve_device(settings.DEVICE)

    try:
        _set_status("loading", target=f"Translation model: {model_name}")
        translation_services.load_model(resolved_device, model_name)
    except Exception as e:
        _set_status("error", error=f"Failed to load NLLB model '{model_name}': {str(e)}")
        return

    _set_status("ready")
