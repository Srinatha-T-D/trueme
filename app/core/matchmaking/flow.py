import logging
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.redis_client import redis_client
from app.services.matchmaking import add_user_to_pool, match_users
from app.services.billing import start_paid_session, can_start_session
from app.core.sessions.lifecycle import start_session

logger = logging.getLogger("trueme.matchmaking.flow")


class MatchError(Exception):
    pass


async def find_match(telegram_id: int) -> tuple[int, int]:
    logger.info(f"[MATCHMAKING] /find called by {telegram_id}")

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user or not user.role:
            raise MatchError("PROFILE_INCOMPLETE")

        if user.role != "male":
            raise MatchError("ONLY_MALE_CAN_FIND")

        if not await can_start_session(db=db, male_id=user.id):
            logger.info(
                f"[MATCHMAKING] Reject /find: insufficient stars for {user.id}"
            )
            raise MatchError("INSUFFICIENT_STARS")

        await redis_client.set(f"user:{user.id}:role", user.role)

        if await redis_client.get(f"user:{user.id}:in_session") == "1":
            raise MatchError("ALREADY_IN_SESSION")

        await add_user_to_pool(user.id)

        match = await match_users()
        if not match:
            raise MatchError("NO_MATCH")

        male_id, female_id = match

        # 🔒 BILLING
        session = await start_paid_session(
            db=db,
            male_id=male_id,
            female_id=female_id
        )

        # ✅ CRITICAL FIX — COMMIT BEFORE REDIS SESSION
        await db.commit()
        await db.refresh(session)

        logger.info(
            f"[MATCHMAKING] DB session committed id={session.id}"
        )

        # 🔥 NOW start Redis session
        await start_session(male_id, female_id)

        logger.info(
            f"[MATCHMAKING] Session started male={male_id} female={female_id}"
        )

        return male_id, female_id
