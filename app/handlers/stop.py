from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.sessions.lifecycle import stop_session

router = Router()


# =====================================================
# KEYBOARDS
# =====================================================

def male_post_chat_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔎 Next Chat",
                    callback_data="next_chat"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⭐ Add to Favorites",
                    callback_data="fav_user"
                ),
                InlineKeyboardButton(
                    text="🚨 Report User",
                    callback_data="report_user"
                )
            ]
        ]
    )


def female_post_chat_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚨 Report User",
                    callback_data="report_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Session Stats",
                    callback_data="session_stats"
                )
            ]
        ]
    )


# =====================================================
# STOP / NEXT HANDLER
# =====================================================

@router.message(Command("stop"))
@router.message(Command("next"))
async def stop_handler(message: types.Message):

    telegram_id = message.from_user.id

    # ----------------------------------
    # Resolve Telegram → DB User
    # ----------------------------------
    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

        if not user:
            await message.answer("⚠️ User not found.")
            return

        user_role = user.role
        user_db_id = user.id

    # ----------------------------------
    # Stop Session (core lifecycle)
    # ----------------------------------
    partner_db_id = await stop_session(user_db_id)

    # ----------------------------------
    # Notify Partner (if exists)
    # ----------------------------------
    if partner_db_id:
        async with AsyncSessionLocal() as db:
            partner = await db.get(User, partner_db_id)

        if partner:
            if partner.role == "male":
                await message.bot.send_message(
                    partner.telegram_id,
                    "⛔ Partner left the chat.",
                    reply_markup=male_post_chat_keyboard()
                )
            else:
                await message.bot.send_message(
                    partner.telegram_id,
                    "⛔ Partner left the chat.\n\n"
                    "You are still ONLINE and will auto-connect when a male searches.",
                    reply_markup=female_post_chat_keyboard()
                )

    # ----------------------------------
    # Self Response (Role Based)
    # ----------------------------------
    if user_role == "male":
        await message.answer(
            "⛔ Chat ended.",
            reply_markup=male_post_chat_keyboard()
        )
    else:
        await message.answer(
            "⛔ Chat ended.\n\n"
            "You are still ONLINE and will auto-connect when a male searches.",
            reply_markup=female_post_chat_keyboard()
        )
