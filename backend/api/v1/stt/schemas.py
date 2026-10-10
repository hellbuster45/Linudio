from pydantic import BaseModel
from core.validation import VideoId

class Speech_Synthesis(BaseModel):
    video_id: VideoId