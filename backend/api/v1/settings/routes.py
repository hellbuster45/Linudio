from fastapi import APIRouter
from .schemas import DeviceUpdateRequest
from .services import get_device_info, set_device

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/device")
def get_device():
    return get_device_info()

@router.post("/device")
def update_device(request: DeviceUpdateRequest):
    return set_device(request.device)
