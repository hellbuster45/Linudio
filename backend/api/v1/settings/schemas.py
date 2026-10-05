from pydantic import BaseModel

class DeviceUpdateRequest(BaseModel):
    device: str  # "cpu", "cuda", or "auto"
