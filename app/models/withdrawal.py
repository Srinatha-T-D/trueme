from sqlalchemy import Column, Integer, Numeric, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(Numeric)
    status = Column(String(20), default="pending")
    screenshot_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime)
