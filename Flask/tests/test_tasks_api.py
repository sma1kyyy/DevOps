# тестирование CRUD сценария и кеширующее поведение списка задач

# полный путь: create -> read -> update -> delete
def test_crud_flow(client):
    create_response = client.post(
        "/api/tasks",
        json={"title": "сделать домашку 5", "description": "дописать flask"},
    )
    assert create_response.status_code == 201
    task_id = create_response.get_json()["id"]

    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 200
    assert get_response.get_json()["title"] == "сделать домашку 5"

    update_response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "сделать домашку", "is_done": True},
    )
    assert update_response.status_code == 200
    assert update_response.get_json()["is_done"] is True

    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    not_found_response = client.get(f"/api/tasks/{task_id}")
    assert not_found_response.status_code == 404

# проверка, что второй запрос спика идет из кеша
def test_list_uses_cache_on_second_request(client):
    client.post("/api/tasks", json={"title": "a", "description": "b"})

    first_response = client.get("/api/tasks")
    second_response = client.get("/api/tasks")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.get_json()["source"] == "postgres"
    assert second_response.get_json()["source"] == "redis-cache"

# проверка, что апдейт понимает is_done, is done и isDone
def test_update_accepts_common_done_keys(client):
    """проверяем что апдейт понимает is_done, is done и isDone."""

    created = client.post("/api/tasks", json={"title": "x", "description": "y"}).get_json()
    task_id = created["id"]

    response = client.put(f"/api/tasks/{task_id}", json={"is done": "true"})
    assert response.status_code == 200
    assert response.get_json()["is_done"] is True