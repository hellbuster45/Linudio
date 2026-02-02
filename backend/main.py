from fastapi import FastAPI
from api.v1.videos.routes import router as video_router
# from api.text_to_speech import router as tts_router

app = FastAPI()

app.include_router(video_router)
# app.include(tts_router)

@app.get("/")
def root():
    return{"status": "app running yay! :D"}