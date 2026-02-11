from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class TelegramStarsLedger(Base):
    __tablename__ = "telegram_stars_ledger"

    id = Column(Integer, primary_key=True)
    telegram_event_id = Column(String, unique=True, nullable=False)
    telegram_user_id = Column(BigInteger, nullable=False)
    stars = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
