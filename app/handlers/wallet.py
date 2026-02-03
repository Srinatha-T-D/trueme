from aiogram import Router, types
from aiogram.filters import Command

from app.core.payments.wallet import request_withdrawal, WalletError

router = Router()


@router.message(Command("withdraw"))
async def request_withdrawal_handler(message: types.Message):
    try:
        await request_withdrawal(message.from_user.id)
    except WalletError:
        await message.answer("❌ No withdrawable balance.")
        return

    await message.answer(
        "💸 Withdrawal request submitted.\n"
        "Admin will process and pay you."
    )
