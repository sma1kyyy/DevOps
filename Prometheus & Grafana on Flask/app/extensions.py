# инициализация расширения flask отдельно, чтобы обойти циклы импортов

from flask_sqlalchemy import SQLAlchemy

db=SQLAlchemy()