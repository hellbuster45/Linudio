from fastapi import APIRouter
from .schemas import DeviceUpdateRequest, WhisperModelUpdateRequest, NllbModelUpdateRequest
from .services import get_device_info, set_device, set_whisper_model, set_nllb_model

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/device")
def get_device():
    return get_device_info()

@router.post("/device")
def update_device(request: DeviceUpdateRequest):
    return set_device(request.device)

@router.post("/whisper_model")
def update_whisper_model(request: WhisperModelUpdateRequest):
    return set_whisper_model(request.model_size)

@router.post("/nllb_model")
def update_nllb_model(request: NllbModelUpdateRequest):
    return set_nllb_model(request.model_name)
