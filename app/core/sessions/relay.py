from datetime import datetime, timedelta
from sqlalchemy import select, desc
import logging

from app.database import AsyncSessionLocal
from app.models.session import ChatSession
from app.models.user import User
from app.services.chat_session import get_partner
from app.core.sessions.lifecycle import stop_session
from app.services.billing import finalize_session

logger = logging.getLogger("trueme.relay")

CHAT_MINUTES = 30  # 49 Stars = 30 Minutes


class RelayResult:
    NONE = "none"
    RELAY = "relay"
    EXPIRED = "expired"


async def relay_text(telegram_id: int, text: str):
    logger.info(f"[RELAY] Incoming message from TG {telegram_id}: {text}")

    async with AsyncSessionLocal() as db:

        # Convert telegram_id → DB ID
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            logger.warning(f"[RELAY] No DB user found for telegram_id={telegram_id}")
            return RelayResult.NONE, None

        db_user_id = user.id
        logger.info(f"[RELAY] telegram_id={telegram_id} → db_id={db_user_id}")

        # Get partner from Redis pairing
        partner_db_id = await get_partner(db_user_id)

        if not partner_db_id:
            logger.warning(f"[RELAY] No partner found for db_id={db_user_id}")
            return RelayResult.NONE, None

        # 🔥 FIX 1: Always get LATEST active session
        session = await db.scalar(
            select(ChatSession)
            .where(
                (
                    (ChatSession.male_id == db_user_id)
                    | (ChatSession.female_id == db_user_id)
                ),
                ChatSession.ended_at.is_(None)
            )
            .order_by(desc(ChatSession.id))   # ← critical fix
        )

        if not session:
            logger.warning(f"[RELAY] No active session for db_id={db_user_id}")
            await stop_session(db_user_id)
            return RelayResult.NONE, None

        logger.info(
            f"[RELAY] Active session id={session.id} started_at={session.started_at}"
        )

        # Expiry check
        expiry = session.started_at + timedelta(minutes=CHAT_MINUTES)

        if datetime.utcnow() >= expiry:
            logger.warning(f"[RELAY] Session expired for session_id={session.id}")

            # 🔥 FIX 2: Use NEW DB session for finalize to avoid nested transaction
            async with AsyncSessionLocal() as new_db:
                await finalize_session(new_db, session.id)

            await stop_session(db_user_id)

            partner = await db.get(User, partner_db_id)
            partner_tg = partner.telegram_id if partner else None

            return RelayResult.EXPIRED, partner_tg

        # Convert partner DB ID → telegram_id
        partner = await db.get(User, partner_db_id)

        if not partner:
            logger.warning(f"[RELAY] Partner missing id={partner_db_id}")
            return RelayResult.NONE, None

        logger.info(
            f"[RELAY] Relaying message db:{db_user_id} → db:{partner_db_id}"
        )

        return RelayResult.RELAY, partner.telegram_id
