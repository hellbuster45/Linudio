from fastapi import FastAPI
from api.v1.videos.routes import router as video_router
from api.v1.stt.routes import router as synthesize_router

app = FastAPI()

app.include_router(video_router)
app.include_router(synthesize_router)

@app.get("/")
def root():
    return{"status": "app running yay! :D"}