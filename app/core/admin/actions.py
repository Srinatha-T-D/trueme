from sqlalchemy import select
from sqlalchemy.sql import func

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.withdrawal import Withdrawal


class AdminError(Exception):
    pass


# -------------------------
# FEMALE VERIFICATION
# -------------------------
async def approve_female(telegram_id: int):
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            raise AdminError("USER_NOT_FOUND")

        if user.role != "female":
            raise AdminError("NOT_FEMALE")

        if user.is_verified:
            raise AdminError("ALREADY_VERIFIED")

        user.is_verified = True
        await db.commit()


# -------------------------
# WITHDRAWAL PAID
# -------------------------
async def mark_withdrawal_paid(withdrawal_id: int):
    async with AsyncSessionLocal() as db:
        withdrawal = await db.get(Withdrawal, withdrawal_id)

        if not withdrawal:
            raise AdminError("WITHDRAWAL_NOT_FOUND")

        if withdrawal.status == "paid":
            raise AdminError("ALREADY_PAID")

        withdrawal.status = "paid"
        withdrawal.paid_at = func.now()
        await db.commit()
