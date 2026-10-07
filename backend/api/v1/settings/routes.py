from fastapi import APIRouter, BackgroundTasks
from .schemas import DeviceUpdateRequest, WhisperModelUpdateRequest, NllbModelUpdateRequest
from .services import (
    get_device_info,
    get_status,
    set_device,
    set_whisper_model,
    set_nllb_model,
    validate_device,
    validate_whisper_model,
    validate_nllb_model,
)

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/device")
def get_device():
    return get_device_info()

@router.get("/status")
def status():
    return get_status()

@router.post("/device")
def update_device(request: DeviceUpdateRequest, background_tasks: BackgroundTasks):
    error = validate_device(request.device)
    if error:
        return {"location": "SETTINGS", "error": error}

    background_tasks.add_task(set_device, request.device)
    return {"status": "loading"}

@router.post("/whisper_model")
def update_whisper_model(request: WhisperModelUpdateRequest, background_tasks: BackgroundTasks):
    error = validate_whisper_model(request.model_size)
    if error:
        return {"location": "SETTINGS", "error": error}

    background_tasks.add_task(set_whisper_model, request.model_size)
    return {"status": "loading"}

@router.post("/nllb_model")
def update_nllb_model(request: NllbModelUpdateRequest, background_tasks: BackgroundTasks):
    error = validate_nllb_model(request.model_name)
    if error:
        return {"location": "SETTINGS", "error": error}

    background_tasks.add_task(set_nllb_model, request.model_name)
    return {"status": "loading"}
