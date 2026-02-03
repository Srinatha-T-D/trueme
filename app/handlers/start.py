from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery,
)

from app.core.users.registration import ensure_user_exists

router = Router()


def role_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨 Male",
                    callback_data="role_select:male"
                ),
                InlineKeyboardButton(
                    text="👩 Female",
                    callback_data="role_select:female"
                ),
            ]
        ]
    )


@router.message(CommandStart())
async def start_handler(message: types.Message):
    # Ensure user exists (minimal, safe)
    await ensure_user_exists(
        telegram_id=message.from_user.id
    )

    await message.answer(
        "👋 <b>Welcome to TRUEME!</b>\n\n"
        "Please choose your role to continue:",
        reply_markup=ReplyKeyboardRemove(),
    )

    await message.answer(
        "Select your role:",
        reply_markup=role_keyboard(),
    )


@router.callback_query(lambda c: c.data.startswith("role_select:"))
async def role_selected(callback: CallbackQuery):
    role = callback.data.split(":")[1]

    # Remove loading animation
    await callback.answer()

    if role == "male":
        await callback.message.answer(
            "👨 <b>Male profile selected</b>\n\n"
            "You can now start finding matches using /find."
        )

    elif role == "female":
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔐 Verify on Website",
                        url="https://admin.athe.co.in/verify/female",
                    )
                ]
            ]
        )

        await callback.message.answer(
            "👩 <b>Female verification required</b>\n\n"
            "To keep TRUEME safe, female users must complete verification "
            "securely on our website.\n\n"
            "👇 Tap below to continue:",
            reply_markup=keyboard,
        )
