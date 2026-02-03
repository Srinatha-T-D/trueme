from sqlalchemy import Column, Integer
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FemaleStats(Base):
    __tablename__ = "female_stats"

    user_id = Column(Integer, primary_key=True)
    level = Column(Integer, default=1)
    total_sessions = Column(Integer, default=0)
