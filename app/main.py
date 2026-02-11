from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import Update

from app.config import BOT_TOKEN
from app.config import ADMIN_SECRET
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# -------------------------
# FASTAPI APP (MUST BE FIRST)
# -------------------------
app = FastAPI()

# -------------------------
# BOT & DISPATCHER
# -------------------------
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# -------------------------
# TELEGRAM HANDLERS
# -------------------------
from app.handlers.start import router as start_router
from app.handlers.profile import router as profile_router
from app.handlers.find import router as find_router
from app.handlers.chat import router as chat_router
from app.handlers.stop import router as stop_router
from app.handlers.admin import router as admin_router
from app.handlers.debug import router as debug_router
from app.handlers.post_chat_actions import router as post_chat_router

dp.include_router(start_router)
dp.include_router(profile_router)
dp.include_router(find_router)
dp.include_router(chat_router)
dp.include_router(stop_router)
dp.include_router(admin_router)
dp.include_router(debug_router)
dp.include_router(post_chat_router)

# -------------------------
# STARS WEBHOOK
# -------------------------
from app.webhooks.stars import router as stars_router
app.include_router(stars_router)

# -------------------------
# ADMIN API + UI (FASTAPI)
# -------------------------
from app.admin.api import router as admin_api_router
from app.admin.ui import router as admin_ui_router
from app.admin.auth import router as admin_auth_router
from app.admin.routes import router as admin_routes_router
from app.verification.routes import router as verification_router

app.include_router(admin_ui_router, prefix="/admin")
app.include_router(admin_api_router, prefix="/admin")
app.include_router(admin_auth_router, prefix="/admin")
app.include_router(verification_router)
app.include_router(admin_routes_router)

app.add_middleware(
    SessionMiddleware,
    secret_key=ADMIN_SECRET,
    session_cookie="trueme_admin",
    https_only=True,
)

# -------------------------
# TELEGRAM WEBHOOK
# -------------------------
@app.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.model_validate(data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Telegram update")

    await dp.feed_update(bot, update)
    return {"ok": True}

# -------------------------
# STARTUP / SHUTDOWN
# -------------------------
@app.on_event("startup")
async def on_startup():
    print("🚀 TRUEME BOT STARTED (WEBHOOK MODE)")
    await dp.emit_startup()

@app.on_event("shutdown")
async def on_shutdown():
    print("🛑 TRUEME BOT SHUTDOWN")
    await dp.emit_shutdown()
    await bot.session.close()
