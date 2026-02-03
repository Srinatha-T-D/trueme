from typing import Optional, Tuple
from app.redis_client import redis_client

MALE_QUEUE = "queue:male"
FEMALE_SET = "online:female"
BUSY_SET = "busy:users"


# -------------------------
# QUEUE MANAGEMENT
# -------------------------
async def add_male_to_queue(user_id: int):
    await redis_client.rpush(MALE_QUEUE, user_id)


async def set_female_online(user_id: int):
    await redis_client.sadd(FEMALE_SET, user_id)


async def set_female_offline(user_id: int):
    await redis_client.srem(FEMALE_SET, user_id)


# -------------------------
# ATOMIC MATCH (LUA)
# -------------------------
MATCH_LUA = """
local male = redis.call('LPOP', KEYS[1])
if not male then
    return nil
end

local female = redis.call('SPOP', KEYS[2])
if not female then
    redis.call('LPUSH', KEYS[1], male)
    return nil
end

-- prevent double matches
if redis.call('SISMEMBER', KEYS[3], male) == 1
   or redis.call('SISMEMBER', KEYS[3], female) == 1 then
    redis.call('LPUSH', KEYS[1], male)
    redis.call('SADD', KEYS[2], female)
    return nil
end

redis.call('SADD', KEYS[3], male, female)
return { male, female }
"""


async def match_users() -> Optional[Tuple[int, int]]:
    result = await redis_client.eval(
        MATCH_LUA,
        3,
        MALE_QUEUE,
        FEMALE_SET,
        BUSY_SET
    )

    if not result:
        return None

    male, female = result
    return int(male), int(female)


# -------------------------
# RELEASE USERS
# -------------------------
async def release_users(user_a: int, user_b: int):
    await redis_client.srem(BUSY_SET, user_a, user_b)
