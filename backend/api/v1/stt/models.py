from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.sql import func
from database import Base

class Transcripts(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key = True, index = True)
    video_id = Column(String, unique = True, index = True)
    src_lang = Column(String, nullable=False)
    original_transcript = Column(JSON)
    translated_transcript = Column(JSON)
    tgt_lang = Column(String)
    probability = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
