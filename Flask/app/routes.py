# роуты апи с полным набором CRUD

from flask import Blueprint, jsonify, request

from .cache import get_cached_tasks_list, invalidate_tasks_cache, set_cached_tasks_list
from .extensions import db
from .models import Task

api_bp = Blueprint("api", __name__, url_prefix="/api")

# блюпринт гета проверки на живучесть
@api_bp.get("/health")
def healthcheck():
    return jsonify({"status": "ok"})

# список задач, сначала редис потом постгря
@api_bp.get("/tasks")
def list_tasks():
    cached_payload = get_cached_tasks_list()
    if cached_payload is not None:
        return jsonify({"source": "redis-cache", "items": cached_payload})

    tasks = Task.query.order_by(Task.id.asc()).all()
    serialized_tasks = [task.to_dict() for task in tasks]
    set_cached_tasks_list(serialized_tasks)
    return jsonify({"source": "postgres", "items": serialized_tasks})

# создание задачи и потом сразу инвалидация кеша списком
@api_bp.post("/tasks")
def create_task():
    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()

    if not title:
        return jsonify({"error": "title is required"}), 400

    task = Task(title=title, description=description)
    db.session.add(task)
    db.session.commit()
    invalidate_tasks_cache()
    return jsonify(task.to_dict()), 201

# для чтения одной задачи по id
@api_bp.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = db.get_or_404(Task, task_id)
    return jsonify(task.to_dict())

# для обновления задачи целиком
@api_bp.put("/tasks/<int:task_id>")
def update_task(task_id: int):
    task = db.get_or_404(Task, task_id)
    payload = request.get_json(silent=True) or {}

    if "title" in payload:
        next_title = (payload.get("title") or "").strip()
        if not next_title:
            return jsonify({"error": "title must not be empty"}), 400
        task.title = next_title

    if "description" in payload:
        task.description = (payload.get("description") or "").strip()
    
    # поддержка несколько вариантов ключа
    done_value = None
    for possible_key in ("is_done", "is done", "isDone"):
        if possible_key in payload:
            done_value = payload[possible_key]
            break

    if done_value is not None:
        task.is_done = str(done_value).strip().lower() in {"1", "true", "yes", "y", "on"}

    db.session.commit()
    invalidate_tasks_cache()
    return jsonify(task.to_dict())

# удаление задачи и чистка кеша
@api_bp.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    invalidate_tasks_cache()
    return "", 204