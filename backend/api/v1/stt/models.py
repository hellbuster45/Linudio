from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from database import Base

class Transcripts(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key = True, index = True)
    video_id = Column(String, unique = True, index = True)
    original_transcript = Column(Text)
    translated_transcript = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TranscriptJobs(Base):
    __tablename__ = "transcript_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    video_id = Column(String, index=True)
    status = Column(String, default="pending")   # pending|processing|completed|failed
    progress = Column(Float, default=0.0)         # 0.0..1.0
    error_message = Column(Text, nullable=True)
    result = Column(Text, nullable=True)          # JSON string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)