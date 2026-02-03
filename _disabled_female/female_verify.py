from aiogram import Router, types
from aiogram.filters import Command

router = Router()

# ==================================================
# FEMALE VERIFICATION (DEPRECATED – WEB ONLY NOW)
# ==================================================

@router.message(Command("verify"))
async def deprecated_female_verification(message: types.Message):
    await message.answer(
        "👩 <b>Female Verification Update</b>\n\n"
        "Female verification is now done securely on our website.\n\n"
        "🔐 Please complete verification here:\n"
        "👉 https://admin.athe.co.in/verify/female\n\n"
        "This helps us keep TRUEME safe and reliable 💙"
    )
