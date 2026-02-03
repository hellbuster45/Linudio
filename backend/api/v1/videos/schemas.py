from pydantic import BaseModel

class YoutubeVideo(BaseModel):
    url: str