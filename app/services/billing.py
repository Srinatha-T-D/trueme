from datetime import datetime
import os
from sqlalchemy import select

from app.models.session import ChatSession
from app.models.wallet import Wallet
from app.models.female_stats import FemaleStats
from app.services.commission import get_commission_rate


# =========================================================
# CONSTANTS
# =========================================================

SESSION_DURATION_MINUTES = 30
TELEGRAM_FEE_RATE = 0.30

TEST_PRICING = os.getenv("TRUEME_TEST_PRICING", "false").lower() == "true"

# Cost is in MINUTES (wallet.paid_minutes)
MALE_SESSION_COST_MINUTES = 1 if TEST_PRICING else 49


# =========================================================
# PRE-CHECK (READ ONLY)
# =========================================================

async def can_start_session(db, male_id: int) -> bool:
    wallet = await db.get(Wallet, male_id)
    if not wallet:
        return False
    return wallet.paid_minutes >= MALE_SESSION_COST_MINUTES


# =========================================================
# START SESSION (NO TRANSACTION HERE)
# =========================================================

async def start_paid_session(db, male_id: int, female_id: int) -> ChatSession:
    """
    Deducts minutes and creates a session.
    Assumes caller already owns the transaction.
    """

    male_wallet = await db.get(Wallet, male_id, with_for_update=True)
    if not male_wallet or male_wallet.paid_minutes < MALE_SESSION_COST_MINUTES:
        raise ValueError("INSUFFICIENT_MINUTES")

    # 🔒 Deduct upfront
    male_wallet.paid_minutes -= MALE_SESSION_COST_MINUTES

    # ✅ ONLY session fields that EXIST in model
    session = ChatSession(
        male_id=male_id,
        female_id=female_id,
        started_at=datetime.utcnow(),
        completed=False,
    )

    db.add(session)
    return session


# =========================================================
# FINALIZE SESSION (OWNS TRANSACTION)
# =========================================================

async def finalize_session(db, session_id: int):
    """
    Finalizes session.
    Assumes caller already owns transaction.
    DO NOT start a new transaction here.
    """

    session = await db.get(ChatSession, session_id, with_for_update=True)
    if not session or session.completed:
        return

    now = datetime.utcnow()
    session.ended_at = now
    session.completed = True

    # ⏱ Actual minutes used
    duration_seconds = (now - session.started_at).total_seconds()
    actual_minutes = max(
        1,
        min(int(duration_seconds // 60), SESSION_DURATION_MINUTES)
    )

    # 💰 Platform revenue model
    platform_gross = MALE_SESSION_COST_MINUTES
    platform_net = platform_gross * (1 - TELEGRAM_FEE_RATE)

    per_minute_value = platform_net / SESSION_DURATION_MINUTES
    female_earning = per_minute_value * actual_minutes

    # 📊 Female stats
    stats = await db.scalar(
        select(FemaleStats)
        .where(FemaleStats.user_id == session.female_id)
        .with_for_update()
    )

    if stats:
        stats.total_sessions += 1
        if stats.total_sessions >= 3000:
            stats.level = 3
        elif stats.total_sessions >= 1200:
            stats.level = 2

        female_earning *= get_commission_rate(stats.level)

    # 👛 Female wallet
    female_wallet = await db.get(
        Wallet, session.female_id, with_for_update=True
    )

    if female_wallet:
        female_wallet.pending_balance += female_earning
        female_wallet.lifetime_earnings += female_earning
