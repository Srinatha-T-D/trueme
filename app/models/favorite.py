from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(Integer, primary_key=True)
    male_id = Column(Integer, nullable=False)
    female_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
