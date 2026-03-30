import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

_redis_pool: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def redis_get(key: str) -> Optional[Any]:
    r = get_redis()
    value = await r.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value


async def redis_set(key: str, value: Any, ttl: int = settings.session_ttl) -> None:
    r = get_redis()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    await r.set(key, serialized, ex=ttl)


async def redis_delete(key: str) -> None:
    r = get_redis()
    await r.delete(key)


async def redis_publish(channel: str, message: Any) -> None:
    r = get_redis()
    await r.publish(channel, json.dumps(message))
