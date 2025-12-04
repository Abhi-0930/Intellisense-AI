# app/core/redis_client.py
import os
import redis

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port = int(os.getenv("REDIS_PORT", 6379)),
    db = 0,
    decode_responses = True # return str  instead of bytes
)

