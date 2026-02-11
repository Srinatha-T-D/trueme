from aiogram import Router, types
from aiogram.types import CallbackQuery
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User

router = Router()


@router.callback_query(lambda c: c.data == "next_chat")
async def next_chat_handler(callback: CallbackQuery):

    await callback.answer()

    await callback.message.answer(
        "🔎 Searching for next chat...\n\nUse /find"
    )


@router.callback_query(lambda c: c.data == "fav_user")
async def fav_user_handler(callback: CallbackQuery):

    await callback.answer("⭐ Added to favorites")

    await callback.message.answer(
        "⭐ User added to favorites."
    )


@router.callback_query(lambda c: c.data == "report_user")
async def report_user_handler(callback: CallbackQuery):

    await callback.answer("🚨 Report submitted")

    await callback.message.answer(
        "🚨 Report submitted. Admin will review."
    )


@router.callback_query(lambda c: c.data == "session_stats")
async def session_stats_handler(callback: CallbackQuery):

    await callback.answer()

    telegram_id = callback.from_user.id

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

    if not user:
        await callback.message.answer("Stats unavailable.")
        return

    await callback.message.answer(
        "📊 Session Summary\n\n"
        "💰 Earnings: Calculating...\n"
        "⏱ Time spent: Calculating..."
    )
