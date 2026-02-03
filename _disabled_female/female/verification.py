from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


class FemaleVerificationError(Exception):
    pass


async def ensure_female_user(telegram_id: int):
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user or user.role != "female":
            raise FemaleVerificationError("NOT_FEMALE")

        if user.is_verified:
            raise FemaleVerificationError("ALREADY_VERIFIED")


async def mark_pending_verification(telegram_id: int):
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            raise FemaleVerificationError("USER_NOT_FOUND")

        # IMPORTANT: still pending admin approval
        user.is_verified = False
        await db.commit()
