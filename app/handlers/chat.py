from aiogram import Router, types, F

from app.core.sessions.relay import relay_text, RelayResult

router = Router()


@router.message(F.text)
async def relay_message(message: types.Message):
    result, partner_id = await relay_text(
        user_id=message.from_user.id,
        text=message.text,
    )

    if result == RelayResult.NONE:
        return

    if result == RelayResult.EXPIRED:
        await message.bot.send_message(
            message.from_user.id,
            "⏰ Chat ended (10 minutes completed)."
        )
        await message.bot.send_message(
            partner_id,
            "⏰ Chat ended. Thanks for chatting!"
        )
        return

    # RELAY
    await message.bot.send_message(partner_id, message.text)
