from aiogram import Router, types
import logging

from app.core.sessions.relay import relay_text, RelayResult

router = Router()
logger = logging.getLogger("trueme.relay")


@router.message()
async def relay_handler(message: types.Message):
    """
    Relays chat messages between matched users.
    """

    # Ignore commands
    if message.text and message.text.startswith("/"):
        return

    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    result, partner_id = await relay_text(user_id, text)

    if result == RelayResult.NONE:
        return

    if result == RelayResult.EXPIRED:
        try:
            await message.answer(
                "⛔ Chat ended.\n⏱ Session time expired."
            )
            if partner_id:
                await message.bot.send_message(
                    partner_id,
                    "⛔ Chat ended.\n⏱ Session time expired."
                )
        except Exception as e:
            logger.warning(f"[RELAY] Expiry notify failed: {e}")
        return

    # Relay message
    try:
        await message.bot.send_message(
            partner_id,
            text
        )

        logger.info(
            f"[RELAY] {user_id} → {partner_id}: {text}"
        )

    except Exception as e:
        logger.warning(
            f"[RELAY] Failed {user_id} → {partner_id}: {e}"
        )
