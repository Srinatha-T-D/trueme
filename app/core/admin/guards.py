from app.config import ADMIN_TELEGRAM_ID


def ensure_admin(user_id: int):
    if user_id != ADMIN_TELEGRAM_ID:
        raise PermissionError("NOT_ADMIN")
