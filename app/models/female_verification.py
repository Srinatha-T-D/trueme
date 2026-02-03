from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime
from sqlalchemy.sql import func
from app.database import Base


class FemaleVerification(Base):
    __tablename__ = "female_verifications"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(BigInteger, unique=True, nullable=False)
    full_name = Column(String)

    phone_number = Column(String)
    email = Column(String)

    photo_s3_key = Column(Text)

    status = Column(String(20), default="pending")
    # pending | approved | rejected

    rejection_reason = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True))
