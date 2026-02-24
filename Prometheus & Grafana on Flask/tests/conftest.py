# сердце тестов

import sys
from pathlib import Path
import pytest
import json

# корневая папка проекта в пути поиска питона без этого pytest может сказать "ModuleNotFoundError: No module named 'app'" т.к не будет понимать где код
sys.path.append(str(Path(__file__).resolve().parents[1]))

# формально коробочка, которая записывает что все выполнено и отправлено, используется словарик, методы редиски и экземляр, чтобы данные не пропадали
class FakeRedisClient:
    def __init__(self):
        self._data = {}
    
    def get(self, key):
        return self._data.get(key)
    
    def set(self, key, value, ex=None):
        self._data[key] = value
    
    def setex(self, key, ttl, value):
        self._data[key] = value
    
    def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)

fake_redis_instance = FakeRedisClient()

def fake_get_redis_client():
    return fake_redis_instance
# фикстура с scope="function" означает что для каждого нового теста создается чистое приложение
@pytest.fixture(scope="function")
def app(monkeypatch):
    # ОЧИЩАЕМ КЕШ REDIS ПЕРЕД КАЖДЫМ ТЕСТОМ
    fake_redis_instance._data.clear()
    
    # MONKEYPATCH: самое крутое, мы говорим питону "когда код будет просить функцию app.cache.get_redis_client подкинь ему наш fake_get_redis_client вместо ориги", так китайцы обычно делают
    monkeypatch.setattr("app.cache.get_redis_client", fake_get_redis_client)
    # настройки теста
    test_config = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    }
    
    from app import create_app
    from app.extensions import db
    
    test_app = create_app(test_config)
    
    with test_app.app_context():
        db.create_all() # создание на ходу
        yield test_app # передаем прило в тест
        db.drop_all() # сносим все
# фиксатура клиента, позволяет делать запросы к апи без запуска реального веб-сервера
@pytest.fixture()
def client(app):
    return app.test_client()