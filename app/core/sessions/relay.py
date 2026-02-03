from datetime import datetime, timedelta
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.session import ChatSession
from app.services.chat_session import get_partner
from app.core.sessions.lifecycle import stop_session
from app.services.billing import finalize_session

CHAT_MINUTES = 10


class RelayResult:
    NONE = "none"
    RELAY = "relay"
    EXPIRED = "expired"


async def relay_text(user_id: int, text: str):
    partner_id = await get_partner(user_id)
    if not partner_id:
        return RelayResult.NONE, None

    async with AsyncSessionLocal() as db:
        session = await db.scalar(
            select(ChatSession).where(
                (ChatSession.male_id == user_id)
                | (ChatSession.female_id == user_id),
                ChatSession.ended_at.is_(None)
            )
        )

        if not session:
            await stop_session(user_id)
            return RelayResult.NONE, None

        expiry = session.started_at + timedelta(minutes=CHAT_MINUTES)
        if datetime.utcnow() >= expiry:
            await finalize_session(db, session.id)
            await stop_session(user_id)
            return RelayResult.EXPIRED, partner_id

    return RelayResult.RELAY, partner_id
