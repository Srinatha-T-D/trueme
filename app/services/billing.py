from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.session import ChatSession
from app.models.wallet import Wallet
from app.models.female_stats import FemaleStats
from app.services.commission import get_commission_rate

CHAT_MINUTES = 10
STARS_PER_CHAT = 20
TELEGRAM_FEE_RATE = 0.30


# -------------------------
# START PAID SESSION
# -------------------------
async def start_paid_session(db, male_id: int, female_id: int) -> ChatSession:
    """
    Deducts stars upfront and creates a prepaid chat session.
    This function is ATOMIC and SAFE.
    """

    async with db.begin():
        male_wallet = await db.get(Wallet, male_id, with_for_update=True)
        if not male_wallet or male_wallet.balance < STARS_PER_CHAT:
            raise ValueError("INSUFFICIENT_STARS")

        # Deduct upfront
        male_wallet.balance -= STARS_PER_CHAT

        session = ChatSession(
            male_id=male_id,
            female_id=female_id,
            started_at=datetime.utcnow(),
            max_duration_minutes=CHAT_MINUTES,
            prepaid_stars=STARS_PER_CHAT,
            completed=False
        )

        db.add(session)

    return session


# -------------------------
# FINALIZE SESSION
# -------------------------
async def finalize_session(db, session_id: int):
    """
    Finalizes session, credits female earnings.
    Idempotent-safe.
    """

    async with db.begin():

        session = await db.get(ChatSession, session_id, with_for_update=True)

        # Idempotency guard
        if not session or session.completed:
            return

        now = datetime.utcnow()
        session.ended_at = now
        session.completed = True

        # Calculate actual duration
        duration_minutes = min(
            CHAT_MINUTES,
            int((now - session.started_at).total_seconds() / 60)
        )

        # Earnings calculation
        platform_net = STARS_PER_CHAT * (1 - TELEGRAM_FEE_RATE)

        stats = await db.execute(
            select(FemaleStats)
            .where(FemaleStats.user_id == session.female_id)
            .with_for_update()
        )
        stats = stats.scalar_one()

        stats.total_sessions += 1

        # Level upgrades
        if stats.total_sessions >= 3000:
            stats.level = 3
        elif stats.total_sessions >= 1200:
            stats.level = 2

        rate = get_commission_rate(stats.level)
        female_earning = platform_net * rate

        female_wallet = await db.get(
            Wallet, session.female_id, with_for_update=True
        )

        female_wallet.pending_balance += female_earning
        female_wallet.lifetime_earnings += female_earning
