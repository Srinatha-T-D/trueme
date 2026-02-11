import logging
from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery,
)

from sqlalchemy import select

from app.core.users.registration import ensure_user_exists
from app.database import AsyncSessionLocal
from app.models.user import User
from app.redis_client import get_redis
from app.services.matchmaking import add_user_to_pool, remove_user_from_pool

logger = logging.getLogger("trueme.start")

router = Router()


# =========================
# Keyboards
# =========================

def role_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Male", callback_data="role_select:male"),
                InlineKeyboardButton(text="👩 Female", callback_data="role_select:female"),
            ]
        ]
    )


def female_verify_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔐 Verify on Website",
                    url="https://admin.athe.co.in/verify/female",
                )
            ]
        ]
    )


def female_online_keyboard(is_online: bool):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔴 Go Offline" if is_online else "🟢 Go Online",
                    callback_data="female_offline" if is_online else "female_online",
                )
            ]
        ]
    )


# =========================
# /start
# =========================

@router.message(CommandStart())
async def start_handler(message: types.Message):
    telegram_id = message.from_user.id
    await ensure_user_exists(telegram_id=telegram_id)

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

    redis = await get_redis()

    # 🔁 Always backfill role into Redis
    if user.role:
        await redis.set(f"user:{user.id}:role", user.role)
        logger.info(f"[START] Backfilled role={user.role} for user={user.id}")

    # ---------------- FEMALE ----------------
    if user.role == "female":
        if not user.is_verified:
            await message.answer(
                "👩 <b>Female verification required</b>\n\n"
                "Please verify securely on our website:",
                reply_markup=female_verify_keyboard(),
            )
            return

        is_online = await redis.get(f"user:{user.id}:available") == "1"

        await message.answer(
            "👋 <b>Welcome back to TRUEME!</b>\n\n"
            f"Status: {'🟢 Online' if is_online else '🔴 Offline'}",
            reply_markup=female_online_keyboard(is_online),
        )
        return

    # ---------------- MALE ----------------
    if user.role == "male":
        await message.answer(
            "👋 <b>Welcome back to TRUEME!</b>\n\n"
            "Use /find to start matching.",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    # ---------------- NO ROLE ----------------
    await message.answer(
        "👋 <b>Welcome to TRUEME!</b>\n\nPlease choose your role:",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer("Select your role:", reply_markup=role_keyboard())


# =========================
# Role Selection
# =========================

@router.callback_query(lambda c: c.data.startswith("role_select:"))
async def role_selected(callback: CallbackQuery):
    role = callback.data.split(":")[1]
    telegram_id = callback.from_user.id
    await callback.answer()

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )
        user.role = role
        db.add(user)
        await db.commit()

    redis = await get_redis()
    await redis.set(f"user:{user.id}:role", role)

    logger.info(f"[START] User {user.id} selected role={role}")

    if role == "male":
        await callback.message.answer(
            "👨 <b>Male profile selected</b>\n\nUse /find to start matching."
        )
    else:
        await callback.message.answer(
            "👩 <b>Female verification required</b>",
            reply_markup=female_verify_keyboard(),
        )


# =========================
# Female Online / Offline
# =========================

@router.callback_query(lambda c: c.data in ("female_online", "female_offline"))
async def female_toggle(callback: CallbackQuery):
    telegram_id = callback.from_user.id
    await callback.answer()

    async with AsyncSessionLocal() as db:
        user = await db.scalar(
            select(User).where(User.telegram_id == telegram_id)
        )

    redis = await get_redis()

    # 🔥 ENSURE ROLE IS IN REDIS (THIS WAS MISSING)
    await redis.set(f"user:{user.id}:role", "female")

    available_key = f"user:{user.id}:available"

    if callback.data == "female_online":
        await redis.set(available_key, "1")
        await add_user_to_pool(user.id)
        logger.info(f"[START] Female {user.id} ONLINE, role synced, added to pool")
        is_online = True
    else:
        await redis.delete(available_key)
        await remove_user_from_pool(user.id)
        logger.info(f"[START] Female {user.id} OFFLINE, removed from pool")
        is_online = False

    await callback.message.edit_text(
        "🟢 <b>You are now ONLINE</b>" if is_online else "🔴 <b>You are now OFFLINE</b>",
        reply_markup=female_online_keyboard(is_online),
    )
