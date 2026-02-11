from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, nullable=False)
    reported_id = Column(Integer, nullable=False)
    reason = Column(String(255))
    created_at = Column(DateTime, server_default=func.now())

