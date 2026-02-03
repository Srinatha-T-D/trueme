from typing import Optional

from app.services.chat_session import (
    get_partner,
    clear_active_pair,
)
from app.services.matchmaking import release_users


# -------------------------
# START SESSION (RULE)
# -------------------------
async def start_session(user_a: int, user_b: int):
    from app.services.chat_session import set_active_pair
    await set_active_pair(user_a, user_b)


# -------------------------
# STOP SESSION (RULE)
# -------------------------
async def stop_session(user_id: int) -> Optional[int]:
    """
    Ends an active chat session safely.
    Returns partner_id if a session existed.
    """
    partner = await get_partner(user_id)
    if not partner:
        return None

    await clear_active_pair(user_id, partner)
    await release_users(user_id, partner)

    return partner
