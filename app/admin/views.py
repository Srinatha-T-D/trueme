from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.withdrawal import Withdrawal


# -------------------------
# FEMALES WAITING APPROVAL
# -------------------------
async def get_pending_females():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(
                User.role == "female",
                User.is_verified.is_(False)
            )
        )
        users = result.scalars().all()

        return [
            {
                "telegram_id": u.telegram_id,
                "role": u.role,
                "is_verified": u.is_verified,
            }
            for u in users
        ]


# -------------------------
# PENDING WITHDRAWALS
# -------------------------
async def get_pending_withdrawals():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Withdrawal).where(
                Withdrawal.status == "pending"
            )
        )
        rows = result.scalars().all()

        return [
            {
                "id": w.id,
                "user_id": w.user_id,
                "amount": w.amount,
                "status": w.status,
            }
            for w in rows
        ]
