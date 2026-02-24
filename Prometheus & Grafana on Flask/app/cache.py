# утилиты для кеширования в редис, чтобы не дублировать код по роутам

import os
import json
import redis
from flask import current_app

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

def get_redis_client() -> redis.Redis:
    """создаем клиента redis через url из конфига."""

    return redis.from_url(current_app.config["REDIS_URL"], decode_responses=True)

# поднимаем кеш списка задач, если есть и если валиден
def get_cached_tasks_list() -> list[dict] | None:
    raw_value = get_redis_client().get("tasks:list")
    if raw_value is None:
        return None
    return json.loads(raw_value)

# закидываем список задач в редис с ttl
def set_cached_tasks_list(tasks: list[dict]) -> None:
    get_redis_client().setex(
        "tasks:list",
        current_app.config["TASKS_CACHE_TTL"],
        json.dumps(tasks),
    )

# сброс кеша, когда данные поменялись
def invalidate_tasks_cache() -> None:
    get_redis_client().delete("tasks:list")