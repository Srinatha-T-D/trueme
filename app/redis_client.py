import os
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

# ---- Singleton Redis connection ----
_redis = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

# ---- Backward compatibility (OLD CODE) ----
redis_client = _redis

# ---- New async-safe accessor (NEW CODE) ----
async def get_redis():
    return _redis
