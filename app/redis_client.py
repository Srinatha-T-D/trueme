import os
from dotenv import load_dotenv
import redis.asyncio as redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError("REDIS_URL not set")

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)
