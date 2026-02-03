from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    male_id = Column(Integer)
    female_id = Column(Integer)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime)
    stars_used = Column(Integer, default=20)
    completed = Column(Boolean, default=False)
