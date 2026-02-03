from sqlalchemy import select, func
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.session import ChatSession
from app.models.withdrawal import Withdrawal
from app.redis_client import redis_client


async def get_admin_stats():
    async with AsyncSessionLocal() as db:
        total_users = await db.scalar(
            select(func.count()).select_from(User)
        )

        total_females = await db.scalar(
            select(func.count()).where(User.role == "female")
        )

        verified_females = await db.scalar(
            select(func.count()).where(
                User.role == "female",
                User.is_verified.is_(True)
            )
        )

        pending_females = await db.scalar(
            select(func.count()).where(
                User.role == "female",
                User.is_verified.is_(False)
            )
        )

        total_chats = await db.scalar(
            select(func.count()).select_from(ChatSession)
        )

        total_payouts = await db.scalar(
            select(func.coalesce(func.sum(Withdrawal.amount), 0))
        )

        paid_payouts = await db.scalar(
            select(func.coalesce(func.sum(Withdrawal.amount), 0))
            .where(Withdrawal.status == "paid")
        )

        pending_payouts = await db.scalar(
            select(func.coalesce(func.sum(Withdrawal.amount), 0))
            .where(Withdrawal.status == "pending")
        )

    active_chats = await redis_client.hlen("active_chat")

    return {
        "users": {
            "total": total_users,
            "females": total_females,
            "verified_females": verified_females,
            "pending_females": pending_females,
        },
        "chats": {
            "total": total_chats,
            "active": active_chats,
        },
        "payouts": {
            "total": total_payouts,
            "paid": paid_payouts,
            "pending": pending_payouts,
        }
    }

