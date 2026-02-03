from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.wallet import Wallet
from app.models.withdrawal import Withdrawal


class WalletError(Exception):
    pass


async def request_withdrawal(user_id: int):
    async with AsyncSessionLocal() as db:
        wallet = await db.scalar(
            select(Wallet).where(Wallet.user_id == user_id)
        )

        if not wallet or wallet.withdrawable_balance <= 0:
            raise WalletError("NO_BALANCE")

        withdrawal = Withdrawal(
            user_id=user_id,
            amount=wallet.withdrawable_balance,
            status="pending"
        )

        wallet.withdrawable_balance = 0

        db.add(withdrawal)
        await db.commit()
