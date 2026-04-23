from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
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


class TranscriptJobs(Base):
    __tablename__ = "transcript_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    video_id = Column(String, index=True)
    status = Column(String, default="pending")
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
