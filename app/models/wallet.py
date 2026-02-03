from sqlalchemy import Column, Integer, Numeric
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"

    user_id = Column(Integer, primary_key=True)

    # male usage
    free_minutes = Column(Integer, default=15)  # free trial
    referral_minutes = Column(Integer, default=0)
    paid_minutes = Column(Integer, default=0)

    # female earnings
    lifetime_earnings = Column(Numeric, default=0)
    pending_balance = Column(Numeric, default=0)
    withdrawable_balance = Column(Numeric, default=0)
