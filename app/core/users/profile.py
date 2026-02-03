from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User


class ProfileError(Exception):
    pass


async def set_role(telegram_id: int, role: str) -> str:
    """
    Returns:
      - "male_activated"
      - "female_pending"
    Raises:
      - ProfileError
    """
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            raise ProfileError("USER_NOT_FOUND")

        # 🚫 lock role if already verified
        if user.role and user.is_verified:
            raise ProfileError("ROLE_LOCKED")

        if role == "male":
            user.role = "male"
            user.is_verified = True
            await db.commit()
            return "male_activated"

        if role == "female":
            user.role = "female"
            user.is_verified = False
            await db.commit()
            return "female_pending"

        raise ProfileError("INVALID_ROLE")
