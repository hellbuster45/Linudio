from pydantic import BaseModel
from typing import List, Optional
from core.validation import VideoId

class TranscriptSegment(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str

class TextToSpeechRequest(BaseModel):
    video_id: VideoId
    lang_code: str
    segments: List[TranscriptSegment] = None

class DubStatusRequest(BaseModel):
    video_id: VideoId