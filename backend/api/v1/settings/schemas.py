from pydantic import BaseModel

class DeviceUpdateRequest(BaseModel):
    device: str  # "cpu", "cuda", or "auto"

class WhisperModelUpdateRequest(BaseModel):
    model_size: str  # "tiny", "small", "medium", "large-v3", or "large-v3-turbo"

class NllbModelUpdateRequest(BaseModel):
    model_name: str  # e.g. "facebook/nllb-200-distilled-600M"

class SetupRequest(BaseModel):
    device: str  # "cpu", "cuda", or "auto"
    whisper_model: str
    nllb_model: str
    # MeloTTS language codes of the dubbing voices to download now ("EN", "ES", ...).
    # Omit for all of them. A voice left out is downloaded the first time it is used.
    voices: list[str] | None = None
