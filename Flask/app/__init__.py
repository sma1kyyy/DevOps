# приложение flask сборка

from flask import Flask
from .config import Config
from .extensions import db
from .routes import api_bp

# создание и настройка экземпляра приложения
def create_app(test_config: dict | None = None) -> Flask:

    app = Flask(__name__)
    app.config.from_object(Config)

    # точно определяем конфиг
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api_bp)

    # создаем таблицы на старте для стенда
    with app.app_context():
        db.create_all()

    return app