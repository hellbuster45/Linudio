from fastapi import APIRouter
from .schemas import Speech_Synthesis
from .services import transcribe_audio
router = APIRouter(prefix="/synthesize", tags=["Speech Synthesis"])

@router.get("/")
@router.get("/health")
def health():
    return {"status": "Synthesis running !"}

@router.post("/")
def transcribe(request: Speech_Synthesis):
    path = request.file_path
    response = transcribe_audio(path)

    return {"result": response}