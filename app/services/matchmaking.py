import logging
from typing import Optional, Tuple

from app.redis_client import redis_client

logger = logging.getLogger("trueme.matchmaking")


# -------------------------
# Redis key helpers
# -------------------------
def pool_key() -> str:
    return "matchmaking:pool"


def user_role_key(user_id: int) -> str:
    return f"user:{user_id}:role"


def user_in_session_key(user_id: int) -> str:
    return f"user:{user_id}:in_session"


# -------------------------
# Pool operations
# -------------------------
async def add_user_to_pool(user_id: int):
    await redis_client.sadd(pool_key(), user_id)
    logger.info(f"[MATCHMAKING] User {user_id} added to pool")


async def remove_user_from_pool(user_id: int):
    await redis_client.srem(pool_key(), user_id)
    logger.info(f"[MATCHMAKING] User {user_id} removed from pool")


async def get_pool_members():
    members = await redis_client.smembers(pool_key())
    return {int(m) for m in members}


# -------------------------
# Session checks (READ ONLY)
# -------------------------
async def is_user_in_session(user_id: int) -> bool:
    return await redis_client.get(user_in_session_key(user_id)) == "1"


# -------------------------
# Core matcher (internal)
# -------------------------
async def _pick_match() -> Optional[Tuple[int, int]]:
    pool = await get_pool_members()

    males = []
    females = []

    for uid in pool:
        if await is_user_in_session(uid):
            continue

        role = await redis_client.get(user_role_key(uid))
        if role == "male":
            males.append(uid)
        elif role == "female":
            females.append(uid)

    if not males or not females:
        return None

    male = males[0]
    female = females[0]

    logger.info(
        f"[MATCHMAKING] MATCH FOUND → male={male}, female={female}"
    )

    return male, female


# -------------------------
# PUBLIC API (used by flow.py)
# -------------------------
async def match_users() -> Optional[Tuple[int, int]]:
    """
    Compatibility wrapper.
    DO NOT add session logic here.
    """
    return await _pick_match()


# -------------------------
# Release helpers
# -------------------------
async def release_users(user_a: int, user_b: int):
    """
    IMPORTANT:
    - Does NOT touch in_session
    - lifecycle.stop_session() is the ONLY authority
    """
    await remove_user_from_pool(user_a)
    await remove_user_from_pool(user_b)

    logger.info(
        f"[MATCHMAKING] Released users {user_a} and {user_b}"
    )
