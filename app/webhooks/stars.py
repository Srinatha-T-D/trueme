import logging
import hmac
import hashlib
import os
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.wallet import Wallet

logger = logging.getLogger("trueme.stars")

router = APIRouter(prefix="/webhook", tags=["telegram-stars"])

TELEGRAM_STARS_SECRET = os.getenv("TELEGRAM_STARS_SECRET", "dev-secret")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
# TEST MODE: 1 star = 30 minutes
TEST_MINUTES_PER_STAR = 30

# PROD MODE (later): 49 stars = 30 minutes
# We’ll switch later cleanly


# ---------------------------------------------------------
# SIGNATURE VERIFICATION
# ---------------------------------------------------------
def verify_signature(raw_body: bytes, signature: str):
    expected = hmac.new(
        TELEGRAM_STARS_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


# ---------------------------------------------------------
# TELEGRAM STARS WEBHOOK
# ---------------------------------------------------------
@router.post("/stars")
async def telegram_stars_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("X-Telegram-Signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # 🔓 TEST MODE
    if signature != "test":
        verify_signature(raw_body, signature)

    payload = await request.json()

    telegram_user_id = payload.get("telegram_user_id")
    stars = payload.get("stars")

    if not telegram_user_id or not stars:
        raise HTTPException(status_code=400, detail="Invalid payload")

    stars = int(stars)
    minutes_to_add = stars * TEST_MINUTES_PER_STAR

    async with AsyncSessionLocal() as db:
        async with db.begin():

            # 👤 Find user
            user = await db.scalar(
                select(User).where(User.telegram_id == telegram_user_id)
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # 👛 Get or create wallet
            wallet = await db.get(Wallet, user.id, with_for_update=True)
            if not wallet:
                wallet = Wallet(
                    user_id=user.id,
                    free_minutes=15,
                    referral_minutes=0,
                    paid_minutes=0,
                )
                db.add(wallet)
                await db.flush()

                logger.info(
                    f"[STARS] Wallet created for user_id={user.id}"
                )

            # ⏱️ CREDIT PAID MINUTES
            wallet.paid_minutes += minutes_to_add

            logger.info(
                f"[STARS] Credited {minutes_to_add} paid minutes "
                f"(stars={stars}) to user_id={user.id}"
            )

    return {"status": "ok"}
