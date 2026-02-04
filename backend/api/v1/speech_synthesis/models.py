from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Transcripts(Base):
    __tablename__ = "video_transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(String, unique=True, index=True)
    video_title = Column(String)
    thumbnail_url = Column(String)
    audio_path = Column(String)
    transcript = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())