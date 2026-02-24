# точка входа для gunicorn/wsgi

from app import create_app

app = create_app()