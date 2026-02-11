from aiogram import Router, types, F
import logging

from app.core.sessions.relay import relay_text, RelayResult

router = Router()
logger = logging.getLogger("trueme.chat")


# ✅ Only non-command text messages
@router.message(F.text & ~F.text.startswith("/"))
async def relay_message(message: types.Message):
    """
    Relay chat messages between active users.
    Commands are excluded at filter level.
    """

    logger.info(
        f"[CHAT] Relay candidate from {message.from_user.id}: {message.text}"
    )

    # ✅ FIXED: Use positional arguments (not keyword)
    result, partner_id = await relay_text(
        message.from_user.id,
        message.text,
    )

    if result == RelayResult.NONE:
        return

    if result == RelayResult.EXPIRED:
        await message.bot.send_message(
            message.from_user.id,
            "⏰ Chat ended (30 minutes completed)."
        )
        if partner_id:
            await message.bot.send_message(
                partner_id,
                "⏰ Chat ended. Thanks for chatting!"
            )
        return

    # ✅ Normal relay
    if partner_id:
        await message.bot.send_message(partner_id, message.text)
