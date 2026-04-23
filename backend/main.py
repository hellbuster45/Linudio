from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.stt.routes import router as synthesize_router
from api.v1.text_translation.routes import router as translate_router
from api.v1.videos.routes import router as video_router
import sys, asyncio

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


@app.get("/")
def root():
    return {"status": "app running yay! :D"}
