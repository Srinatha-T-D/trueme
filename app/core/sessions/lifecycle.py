from typing import Optional
import logging
from sqlalchemy import select
from datetime import datetime

from app.database import AsyncSessionLocal
from app.models.session import ChatSession
from app.services.chat_session import (
    get_partner,
    clear_active_pair,
    set_active_pair,
)
from app.redis_client import redis_client
from app.services.billing import finalize_session

logger = logging.getLogger("trueme.session.lifecycle")


# -------------------------
# START SESSION
# -------------------------
async def start_session(user_a: int, user_b: int):
    """
    Called only after matchmaking success.
    Does NOT touch pool logic.
    """

    await set_active_pair(user_a, user_b)

    await redis_client.set(f"user:{user_a}:in_session", "1")
    await redis_client.set(f"user:{user_b}:in_session", "1")

    logger.info(
        f"[SESSION] Started session between {user_a} and {user_b}"
    )


# -------------------------
# STOP SESSION (CLEAN ONLY)
# -------------------------
async def stop_session(user_id: int) -> Optional[int]:
    """
    Clean stop:
    - Finalize DB session
    - Clear active pairing
    - Clear in_session flags
    - DOES NOT modify matchmaking pool
    """

    partner = await get_partner(user_id)

    async with AsyncSessionLocal() as db:

        session = await db.scalar(
            select(ChatSession).where(
                (
                    (ChatSession.male_id == user_id)
                    | (ChatSession.female_id == user_id)
                ),
                ChatSession.ended_at.is_(None)
            )
        )

        if session:
            logger.info(
                f"[SESSION] Manual stop → finalizing session id={session.id}"
            )
            await finalize_session(db, session.id)

    # Clear Redis session flags
    await redis_client.delete(f"user:{user_id}:in_session")

    if not partner:
        logger.info(
            f"[SESSION] stop_session: no active partner for {user_id}"
        )
        return None

    # Clear pairing
    await clear_active_pair(user_id, partner)

    # Clear partner flag
    await redis_client.delete(f"user:{partner}:in_session")

    logger.info(
        f"[SESSION] Session stopped for {user_id} and {partner}"
    )

    return partner
