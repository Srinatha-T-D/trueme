from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.services.matchmaking import add_male_to_queue, match_users
from app.services.billing import start_paid_session
from app.core.sessions.lifecycle import start_session


class MatchError(Exception):
    pass


async def find_match(telegram_id: int) -> tuple[int, int]:
    """
    Returns: (male_id, female_id)
    Raises: MatchError
    """
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user or not user.role:
            raise MatchError("PROFILE_INCOMPLETE")

        if user.role == "female" and not user.is_verified:
            raise MatchError("FEMALE_NOT_VERIFIED")

        if user.role != "male":
            raise MatchError("ONLY_MALE_CAN_FIND")

        # 1️⃣ Add to queue
        await add_male_to_queue(telegram_id)

        # 2️⃣ Try match
        match = await match_users()
        if not match:
            raise MatchError("NO_MATCH")

        male_id, female_id = match

        # 3️⃣ Billing (prepaid)
        try:
            await start_paid_session(
                db=db,
                male_id=male_id,
                female_id=female_id
            )
        except ValueError:
            raise MatchError("INSUFFICIENT_STARS")

        # 4️⃣ Start live chat
        await start_session(male_id, female_id)

        return male_id, female_id
