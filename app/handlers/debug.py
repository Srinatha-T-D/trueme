from aiogram import Router, types

router = Router()

@router.callback_query()
async def debug_all_callbacks(callback: types.CallbackQuery):
    print("🔥 CALLBACK RECEIVED:", callback.data)
    await callback.answer("debug")
