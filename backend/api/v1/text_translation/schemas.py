from pydantic import BaseModel
from typing import List, Optional
from core.validation import VideoId

class TranscriptSegment(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str

class TranslationRequest(BaseModel):
    video_id: VideoId
    segments: Optional[List[TranscriptSegment]] = None
    tgt_lang: str