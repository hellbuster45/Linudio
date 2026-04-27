from pydantic import BaseModel
from typing import List, Optional

class TranscriptSegment(BaseModel):
    id: int
    start_time: float
    end_time: float
    text: str

class TranslationRequest(BaseModel):
    video_id: str
    segments: Optional[List[TranscriptSegment]] = None
    tgt_lang: str