from database import Base
from sqlalchemy import Column, String

class DubStatus(Base):
    __tablename__ = "dub_status"

    video_id = Column(String, primary_key=True)
    status = Column(String)