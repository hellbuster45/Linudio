from pydantic import BaseModel

class DeviceUpdateRequest(BaseModel):
    device: str  # "cpu", "cuda", or "auto"

class WhisperModelUpdateRequest(BaseModel):
    model_size: str  # "tiny", "small", "medium", "large-v3", or "large-v3-turbo"

class NllbModelUpdateRequest(BaseModel):
    model_name: str  # e.g. "facebook/nllb-200-distilled-600M"
