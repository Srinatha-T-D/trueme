CHAT_MINUTES = 5
STARS_PER_CHAT = 20

def consume_time(wallet, minutes_needed: int) -> bool:
    """
    Returns True if time was consumed, False if insufficient balance
    """
    # 1. Free trial
    if getattr(wallet, "free_minutes", 0) >= minutes_needed:
        wallet.free_minutes -= minutes_needed
        return True

    # 2. Referral bonus
    if wallet.referral_minutes >= minutes_needed:
        wallet.referral_minutes -= minutes_needed
        return True

    # 3. Paid time (stars equivalent)
    paid_minutes = getattr(wallet, "paid_minutes", 0)
    if paid_minutes >= minutes_needed:
        wallet.paid_minutes -= minutes_needed
        return True

    return False
