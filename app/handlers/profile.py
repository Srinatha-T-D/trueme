from aiogram import Router, types, F

from app.core.users.profile import set_role, ProfileError

router = Router()


@router.callback_query(F.data.in_(["role:male", "role:female"]))
async def role_callback(callback: types.CallbackQuery):
    await callback.answer()  # REQUIRED for webhook mode

    role = callback.data.split(":")[1]
    telegram_id = callback.from_user.id

    try:
        result = await set_role(telegram_id, role)
    except ProfileError as e:
        if str(e) == "USER_NOT_FOUND":
            await callback.message.edit_text("❌ Please use /start first.")
        elif str(e) == "ROLE_LOCKED":
            await callback.message.edit_text("❌ Role already locked.")
        else:
            await callback.message.edit_text("❌ Unable to set role.")
        return

    if result == "male_activated":
        await callback.message.edit_text(
            "✅ <b>Male profile activated</b>\n\n"
            "Use /find 🔍 to start matching."
        )
        return

    if result == "female_pending":
        await callback.message.edit_text(
            "👩 <b>Female registration started</b>\n\n"
            "🔐 Verification required:\n"
            "• Live photo\n"
            "• OTP\n"
            "• Admin approval\n\n"
            "⏳ Follow next steps."
        )
