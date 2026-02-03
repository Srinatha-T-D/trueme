from sqlalchemy import select
from app.models.referral import Referral
from app.models.wallet import Wallet

# 5 Stars = 75 seconds = 1.25 minutes
REFERRAL_BONUS_SECONDS = 75


async def check_and_reward_referral(db, referred_user):
    referral = await db.scalar(
        select(Referral)
        .where(Referral.referred_id == referred_user.id)
        .where(Referral.rewarded.is_(False))
    )

    if not referral:
        return

    # -------------------------
    # SUCCESS CONDITIONS
    # -------------------------
    success = False

    if referred_user.role == "male" and referred_user.has_paid:
        success = True

    if referred_user.role == "female" and referred_user.is_verified:
        success = True

    if not success:
        return

    # -------------------------
    # FETCH REFERRER WALLET
    # -------------------------
    wallet = await db.scalar(
        select(Wallet).where(Wallet.user_id == referral.referrer_id)
    )

    if not wallet:
        return  # safety: wallet not created yet

    # -------------------------
    # APPLY REWARD
    # -------------------------
    wallet.referral_seconds += REFERRAL_BONUS_SECONDS
    referral.rewarded = True
    referral.status = "rewarded"

    await db.commit()
