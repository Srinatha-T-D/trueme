from aiogram import Router, types
from aiogram.filters import Command

from app.core.admin.guards import ensure_admin
from app.core.admin.actions import (
    approve_female,
    mark_withdrawal_paid,
    AdminError,
)

router = Router()


# -------------------------------------------------
# FEMALE VERIFICATION APPROVAL
# -------------------------------------------------
@router.message(Command("verify_female"))
async def verify_female_handler(message: types.Message):
    try:
        ensure_admin(message.from_user.id)
    except PermissionError:
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Usage: /verify_female <telegram_id>")
        return

    telegram_id = int(args[1])

    try:
        await approve_female(telegram_id)
    except AdminError as e:
        if str(e) == "USER_NOT_FOUND":
            await message.answer("❌ User not found.")
        elif str(e) == "NOT_FEMALE":
            await message.answer("❌ User is not female.")
        elif str(e) == "ALREADY_VERIFIED":
            await message.answer("ℹ️ Female already approved.")
        else:
            await message.answer("❌ Verification failed.")
        return

    await message.bot.send_message(
        telegram_id,
        "🎉 <b>Verification Approved!</b>\n\n"
        "You are now live on TRUEME and can receive chats 💬"
    )

    await message.answer("✅ Female verified and activated successfully.")


# -------------------------------------------------
# WITHDRAWAL MARK AS PAID
# -------------------------------------------------
@router.message(Command("mark_paid"))
async def mark_paid_handler(message: types.Message):
    try:
        ensure_admin(message.from_user.id)
    except PermissionError:
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("Usage: /mark_paid <withdrawal_id>")
        return

    withdrawal_id = int(args[1])

    try:
        await mark_withdrawal_paid(withdrawal_id)
    except AdminError as e:
        if str(e) == "WITHDRAWAL_NOT_FOUND":
            await message.answer("❌ Withdrawal not found.")
        elif str(e) == "ALREADY_PAID":
            await message.answer("ℹ️ Withdrawal already marked as PAID.")
        else:
            await message.answer("❌ Unable to mark as paid.")
        return

    await message.answer("✅ Withdrawal marked as PAID.")
