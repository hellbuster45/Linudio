from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class Videos(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(String, unique=True, index = True)
    video_title = Column(String)
    thumbnail_url = Column(String)
    audio_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
