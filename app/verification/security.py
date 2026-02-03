import hashlib
import hmac
from typing import Dict
from app.config import BOT_TOKEN


def verify_telegram_login(data: Dict[str, str]) -> bool:
    """
    Verifies Telegram Login Widget payload.
    """
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(data.items())
    )

    hmac_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac_hash == check_hash
