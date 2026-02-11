from aiogram import Router, types
from aiogram.filters import Command
import logging
from sqlalchemy import select

from app.core.matchmaking.flow import find_match, MatchError
from app.core.sessions.lifecycle import stop_session
from app.database import AsyncSessionLocal
from app.models.user import User

router = Router()
logger = logging.getLogger("trueme.find")


@router.message(Command("find"))
async def find_handler(message: types.Message):
    try:
        # Core returns INTERNAL DB IDs only
        male_id, female_id = await find_match(message.from_user.id)

    except MatchError as e:
        reason = str(e)
        logger.info(f"[FIND] Rejected: {reason}")

        responses = {
            "PROFILE_INCOMPLETE": "⚠️ Please complete your profile using /start.",
            "ONLY_MALE_CAN_FIND": "🚫 Only male users can use /find.",
            "INSUFFICIENT_STARS": "❌ You don’t have enough Stars.\nPlease recharge.",
            "ALREADY_IN_SESSION": "💬 You are already in an active chat.\nUse /stop first.",
            "NO_MATCH": "🔍 Searching for available users...\nPlease wait.",
            "USER_NOT_STARTED": "⚠️ Please press /start to enable chat.",
        }

        await message.answer(responses.get(reason, "❌ Unable to find a match."))
        return

    # 🔹 Convert DB IDs → Telegram IDs
    try:
        async with AsyncSessionLocal() as db:
            male = await db.get(User, male_id)
            female = await db.get(User, female_id)

        if not male or not female:
            logger.error("[FIND] User record missing during notify → rollback")
            await stop_session(male_id)
            return

        male_chat_id = male.telegram_id
        female_chat_id = female.telegram_id

    except Exception as e:
        logger.error(f"[FIND] Failed fetching telegram IDs → rollback: {e}")
        await stop_session(male_id)
        return

    # ---- Notify male ----
    try:
        await message.bot.send_message(
            male_chat_id,
            "💬 Connected!\n⏱ Chat started (30 minutes)."
        )
    except Exception as e:
        logger.error(f"[FIND] Male notify failed → rollback: {e}")
        await stop_session(male_id)
        return

    # ---- Notify female ----
    try:
        await message.bot.send_message(
            female_chat_id,
            "💬 You are now connected.\n⏱ Chat started."
        )
    except Exception as e:
        logger.error(f"[FIND] Female notify failed → rollback: {e}")
        await stop_session(male_id)
        return
