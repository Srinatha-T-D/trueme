from datetime import datetime
from pydantic import BaseModel


class FemalePending(BaseModel):
    telegram_id: int
    username: str | None
    created_at: datetime


class WithdrawalPending(BaseModel):
    id: int
    user_id: int
    amount: int
    created_at: datetime
