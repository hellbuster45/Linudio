import os, sys, asyncio

# Must be set before transformers/faster_whisper/huggingface_hub are imported
# anywhere (including transitively via the route modules below), so all
# downloaded models land in ./models at the repo root instead of ~/.cache.
# Subprocesses we spawn (tts_worker.py, the audio-separator CLI) inherit
# these via the default env=None behavior of asyncio.create_subprocess_exec.
_MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "models"))
os.environ.setdefault("HF_HOME", _MODELS_DIR)
os.environ.setdefault("AUDIO_SEPARATOR_MODEL_DIR", os.path.join(_MODELS_DIR, "audio-separator"))
os.makedirs(os.environ["AUDIO_SEPARATOR_MODEL_DIR"], exist_ok=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api.v1.stt.routes import router as synthesize_router
from api.v1.text_translation.routes import router as translate_router
from api.v1.videos.routes import router as video_router
from api.v1.tts.routes import router as tts_router
from api.v1.settings.routes import router as settings_router

if sys.platform == 'win32':
    # This must happen BEFORE any other asyncio calls
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(video_router)
app.include_router(synthesize_router)
app.include_router(translate_router)
app.include_router(tts_router)
app.include_router(settings_router)

app.mount("/storage", StaticFiles(directory="storage/videos"), name="videos")

@app.get("/")
def root():
    return {"status": "app running yay! :D"}
