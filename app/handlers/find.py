from aiogram import Router, types
from aiogram.filters import Command

from app.core.matchmaking.flow import find_match, MatchError
from app.core.sessions.lifecycle import stop_session

router = Router()


# =========================
# /find COMMAND
# =========================
@router.message(Command("find"))
async def find_handler(message: types.Message):
    try:
        male_id, female_id = await find_match(message.from_user.id)
    except MatchError as e:
        if str(e) == "PROFILE_INCOMPLETE":
            await message.answer(
                "⚠️ Please complete your profile first using /start."
            )
        elif str(e) == "FEMALE_NOT_VERIFIED":
            await message.answer(
                "🛑 Your account is under verification.\n"
                "Please complete verification and wait for admin approval."
            )
        elif str(e) == "INSUFFICIENT_STARS":
            await message.answer(
                "❌ Not enough Stars.\nPlease recharge to continue."
            )
        elif str(e) == "NO_MATCH":
            await message.answer("🔍 Finding a partner...")
        else:
            await message.answer("❌ Unable to find match.")
        return

    # 🔔 Notify both users
    await message.bot.send_message(
        male_id,
        "💬 Connected!\n⏱ Chat started (10 minutes)."
    )
    await message.bot.send_message(
        female_id,
        "💬 You are now connected.\n⏱ Chat started."
    )


# =========================
# /stop and /next
# =========================
@router.message(Command("stop"))
@router.message(Command("next"))
async def stop_handler(message: types.Message):
    partner = await stop_session(message.from_user.id)

    if partner:
        await message.bot.send_message(
            partner,
            "⛔ Partner left the chat."
        )

    await message.answer(
        "⛔ Chat ended.\n\nUse /find to start a new chat."
    )
