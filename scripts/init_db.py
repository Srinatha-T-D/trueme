import asyncio

from sqlalchemy.ext.asyncio import create_async_engine

from app.config import DATABASE_URL
from app.models.user import User
from app.models.wallet import Wallet
from app.models.session import ChatSession
from app.models.female_stats import FemaleStats
from app.models.withdrawal import Withdrawal
from app.models.referral import Referral

# Convert sync DB URL to async
ASYNC_DATABASE_URL = DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)
        await conn.run_sync(Wallet.metadata.create_all)
        await conn.run_sync(ChatSession.metadata.create_all)
        await conn.run_sync(FemaleStats.metadata.create_all)
        await conn.run_sync(Withdrawal.metadata.create_all)
        await conn.run_sync(Referral.metadata.create_all)

    print("✅ All tables created successfully")


if __name__ == "__main__":
    asyncio.run(init_models())
