from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, nullable=False)
    referred_id = Column(Integer, nullable=False)
    referred_role = Column(String(10))
    status = Column(String(20), default="pending")  
    rewarded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
