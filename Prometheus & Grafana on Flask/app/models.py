# модели бд

from datetime import datetime, timezone
from .extensions import db

# модель задачи для наглядного полного CRUD
class Task(db.Model):

    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(120), nullable = False)
    description = db.Column(db.Text, nullable=True, default="")
    is_done = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    def to_dict(self) -> dict:
        # преобразуем модель в dict, чтобы отдать ответ json
        return {
            "id": self.id, 
            "title": self.title,
            "description": self.description,
            "is_done": self.is_done,
            "created_at": self.created_at.isoformat() + "Z",
        }