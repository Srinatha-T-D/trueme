from typing import Optional
from app.redis_client import redis_client

CHAT_KEY = "active_chat"   # Redis hash: user_id -> partner_id


# -------------------------
# LOW-LEVEL PRIMITIVES ONLY
# -------------------------
async def set_active_pair(user_a: int, user_b: int):
    await redis_client.hset(
        CHAT_KEY,
        mapping={
            str(user_a): str(user_b),
            str(user_b): str(user_a),
        }
    )


async def clear_active_pair(user_a: int, user_b: int):
    await redis_client.hdel(CHAT_KEY, str(user_a), str(user_b))


async def get_partner(user_id: int) -> Optional[int]:
    partner = await redis_client.hget(CHAT_KEY, str(user_id))
    return int(partner) if partner else None


async def is_in_chat(user_id: int) -> bool:
    return await redis_client.hexists(CHAT_KEY, str(user_id))
