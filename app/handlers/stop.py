from aiogram import Router, types
from aiogram.filters import Command

from app.core.sessions.lifecycle import stop_session

router = Router()


@router.message(Command("stop"))
@router.message(Command("next"))
async def stop_handler(message: types.Message):
    partner = await stop_session(message.from_user.id)

    if partner:
        await message.bot.send_message(
            partner,
            "⛔ Partner left the chat."
        )

    await message.answer(
        "⛔ Chat ended.\n\nUse /find to start a new chat."
    )
