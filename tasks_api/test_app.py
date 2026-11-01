import os
import sqlite3
import tempfile
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app import app, get_db, init_db


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def client(db_path):
    """Override the get_db dependency so each test gets a fresh, private SQLite DB."""
    def override_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_create_task_happy_path(client):
    response = client.post("/tasks", json={"title": "Write tests", "status": "todo"})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Write tests"
    assert body["status"] == "todo"
    assert body["due_date"] is None
    assert "id" in body
    assert "created_at" in body


def test_create_task_with_due_date(client):
    future = date.today() + timedelta(days=7)
    response = client.post(
        "/tasks",
        json={"title": "Ship it", "status": "doing", "due_date": future.isoformat()},
    )
    assert response.status_code == 201
    assert response.json()["due_date"] == future.isoformat()


def test_get_task(client):
    create = client.post("/tasks", json={"title": "Read", "status": "doing"})
    task_id = create.json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id
    assert response.json()["title"] == "Read"


def test_list_tasks(client):
    client.post("/tasks", json={"title": "A", "status": "todo"})
    client.post("/tasks", json={"title": "B", "status": "doing"})
    response = client.get("/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tasks_filter_by_status(client):
    client.post("/tasks", json={"title": "A", "status": "todo"})
    client.post("/tasks", json={"title": "B", "status": "done"})
    response = client.get("/tasks?status=done")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "done"


def test_list_tasks_limit(client):
    for i in range(5):
        client.post("/tasks", json={"title": f"T{i}", "status": "todo"})
    response = client.get("/tasks?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_update_task(client):
    create = client.post("/tasks", json={"title": "Old", "status": "todo"})
    task_id = create.json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"title": "New", "status": "done"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New"
    assert response.json()["status"] == "done"


def test_delete_task(client):
    create = client.post("/tasks", json={"title": "Bye", "status": "todo"})
    task_id = create.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    # Deleting again must return 404
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Edge cases / error handling
# ---------------------------------------------------------------------------
def test_get_missing_task(client):
    response = client.get("/tasks/does-not-exist")
    assert response.status_code == 404
    assert "error" in response.json()


def test_update_missing_task(client):
    response = client.patch("/tasks/does-not-exist", json={"title": "Nope"})
    assert response.status_code == 404


def test_empty_title(client):
    response = client.post("/tasks", json={"title": "", "status": "todo"})
    assert response.status_code == 422
    assert "error" in response.json()


def test_title_too_long(client):
    response = client.post(
        "/tasks", json={"title": "x" * 201, "status": "todo"}
    )
    assert response.status_code == 422


def test_unknown_status(client):
    response = client.post("/tasks", json={"title": "T", "status": "unknown"})
    assert response.status_code == 422


def test_past_due_date(client):
    yesterday = date.today() - timedelta(days=1)
    response = client.post(
        "/tasks",
        json={"title": "T", "status": "todo", "due_date": yesterday.isoformat()},
    )
    assert response.status_code == 422


def test_past_due_date_on_update(client):
    create = client.post("/tasks", json={"title": "T", "status": "todo"})
    task_id = create.json()["id"]
    yesterday = date.today() - timedelta(days=1)
    response = client.patch(
        f"/tasks/{task_id}",
        json={"due_date": yesterday.isoformat()},
    )
    assert response.status_code == 422


def test_error_shape_is_consistent(client):
    # 404
    response = client.get("/tasks/missing")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message", "status"}
    assert body["error"]["status"] == 404

    # 422
    response = client.post("/tasks", json={"title": "", "status": "todo"})
    assert response.status_code == 422
    body = response.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) == {"code", "message", "status"}
    assert body["error"]["status"] == 422
