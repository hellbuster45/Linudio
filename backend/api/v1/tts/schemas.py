from pydantic import BaseModel
from typing import List, Optional

class TranscriptSegment(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str

class TextToSpeechRequest(BaseModel):
    video_id: str
    lang_code: str
    segments: List[TranscriptSegment] = None