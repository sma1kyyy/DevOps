# конфиг приложения, чтобы не мешать все в кучу

import os

# класс для конфига по минимуму
class Config:

    # строка подключения к postgres из переменных окружения
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://flask:flask@db:5432/flaskdb",
    )

    # чтобы не тратить лишние ресурсы, можно просто отключить события
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # адрес редиса для кеша
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    # ttl кеша списка задач 
    TASKS_CACHE_TTL = int(os.getenv("TASKS_CACHE_TTL", "60"))