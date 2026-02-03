from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User


async def ensure_user_exists(
    telegram_id: int,
    full_name: str | None = None,
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        user = User(
            telegram_id=telegram_id,
        )

        # OPTIONAL: store name only if column exists later
        if hasattr(user, "full_name") and full_name:
            user.full_name = full_name

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user
