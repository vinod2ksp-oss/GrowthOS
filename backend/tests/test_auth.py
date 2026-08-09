import importlib
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import session as session_module


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'app.sqlite3'}")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    importlib.reload(session_module)
    import app.main as main_module
    importlib.reload(main_module)
    from app.db.base import Base
    Base.metadata.create_all(bind=session_module.engine)
    with TestClient(main_module.app) as test_client:
        yield test_client


def register(client: TestClient, email: str) -> None:
    response = client.post("/api/v1/register", json={"email": email, "password": "secret123"})
    assert response.status_code == 200, response.text
    assert response.json()["email"] == email


def token(client: TestClient, email: str) -> str:
    response = client.post("/api/v1/login", json={"email": email, "password": "secret123"})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(value: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {value}"}


def test_authentication_is_strict(client: TestClient) -> None:
    register(client, "user@example.com")
    assert client.post("/api/v1/register", json={"email": "user@example.com", "password": "secret123"}).status_code == 400
    assert client.post("/api/v1/login", json={"email": "user@example.com", "password": "wrongpass"}).status_code == 401
    assert client.get("/api/v1/me").status_code == 403
    access_token = token(client, "user@example.com")
    assert client.get("/api/v1/me", headers=auth(access_token)).status_code == 200


def test_profile_goal_dashboard_and_user_isolation(client: TestClient) -> None:
    register(client, "a@example.com"); register(client, "b@example.com")
    a, b = token(client, "a@example.com"), token(client, "b@example.com")
    profile = client.put("/api/v1/profile", headers=auth(a), json={"nickname": "A", "school": "School", "major": "CS"})
    assert profile.status_code == 200 and profile.json()["nickname"] == "A"
    assert client.get("/api/v1/profile", headers=auth(b)).json() is None
    goal = client.post("/api/v1/goals", headers=auth(a), json={"target_school": "Target", "target_year": 2027})
    assert goal.status_code == 200
    assert client.patch(f"/api/v1/goals/{goal.json()['id']}", headers=auth(b), json={"current_stage": "apply"}).status_code == 404
    assert len(client.get("/api/v1/goals", headers=auth(a)).json()) == 1
    assert len(client.get("/api/v1/goals", headers=auth(b)).json()) == 0
    dashboard = client.get("/api/v1/dashboard", headers=auth(a))
    assert dashboard.status_code == 200 and dashboard.json()["goal_count"] == 1


def test_full_api_smoke_chain_and_permissions(client: TestClient) -> None:
    register(client, "smoke@example.com"); register(client, "other@example.com")
    owner, other = token(client, "smoke@example.com"), token(client, "other@example.com")
    assert client.put("/api/v1/profile", headers=auth(owner), json={"nickname": "Smoke"}).status_code == 200
    assert client.post("/api/v1/goals", headers=auth(owner), json={"target_major": "Engineering"}).status_code == 200
    parent = client.post("/api/v1/tasks", headers=auth(owner), json={"title": "Main", "task_type": "main", "status": "pending"})
    assert parent.status_code == 200
    task_id = parent.json()["id"]
    child = client.post("/api/v1/tasks", headers=auth(owner), json={"title": "Sub", "task_type": "subtask", "parent_task_id": task_id, "status": "pending"})
    assert child.status_code == 200 and child.json()["parent_task_id"] == task_id
    assert client.post("/api/v1/tasks", headers=auth(other), json={"title": "Invalid", "task_type": "subtask", "parent_task_id": task_id}).status_code == 400
    assert client.get(f"/api/v1/tasks/{task_id}", headers=auth(other)).status_code == 404

    started = client.post("/api/v1/timers/start", headers=auth(owner), json={"task_id": task_id})
    assert started.status_code == 200 and started.json()["is_running"] is True
    session_id = started.json()["id"]
    assert client.post(f"/api/v1/timers/{session_id}/pause", headers=auth(other)).status_code == 409
    paused = client.post(f"/api/v1/timers/{session_id}/pause", headers=auth(owner))
    assert paused.status_code == 200 and paused.json()["is_running"] is False
    assert client.post(f"/api/v1/timers/{session_id}/pause", headers=auth(owner)).status_code == 409
    resumed = client.post(f"/api/v1/timers/{session_id}/continue", headers=auth(owner))
    assert resumed.status_code == 200 and resumed.json()["is_running"] is True
    ended = client.post(f"/api/v1/timers/{session_id}/end", headers=auth(owner))
    assert ended.status_code == 200 and ended.json()["end_time"] is not None
    assert client.post(f"/api/v1/timers/{session_id}/continue", headers=auth(owner)).status_code == 409

    upload = client.post("/api/v1/evidences", headers=auth(owner), data={"task_id": task_id, "evidence_type": "result", "description": "done"}, files={"file": ("result.txt", b"result", "text/plain")})
    assert upload.status_code == 200 and upload.json()["task_id"] == task_id
    evidence_id = upload.json()["id"]
    assert client.delete(f"/api/v1/evidences/{evidence_id}", headers=auth(other)).status_code == 404
    assert client.post("/api/v1/evidences", headers=auth(other), data={"task_id": task_id, "evidence_type": "result"}, files={"file": ("x.txt", b"x", "text/plain")}).status_code == 400

    submitted = client.post(f"/api/v1/tasks/{task_id}/evaluations", headers=auth(owner))
    assert submitted.status_code == 201 and submitted.json()["reason"]
    latest = client.get(f"/api/v1/tasks/{task_id}/evaluations/latest", headers=auth(owner))
    assert latest.status_code == 200 and latest.json()["id"] == submitted.json()["id"]
    assert client.get(f"/api/v1/tasks/{task_id}/evaluations/latest", headers=auth(other)).status_code == 404
    dashboard = client.get("/api/v1/dashboard", headers=auth(owner)).json()
    assert dashboard["goal_count"] == 1 and dashboard["task_count"] == 2


def test_alembic_upgrade_head_on_fresh_database(tmp_path: Path) -> None:
    database = tmp_path / "migration.sqlite3"
    env = {**__import__("os").environ, "DATABASE_URL": f"sqlite:///{database}", "JWT_SECRET": "test-secret"}
    result = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=Path(__file__).parents[1], env=env, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(database) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"alembic_version", "users", "user_profiles", "study_goals", "tasks", "learning_sessions", "evidences", "task_evaluations", "materials", "growth_evidences", "growth_attributes", "attribute_evidence_links", "goal_requirements", "weekly_plans", "weekly_plan_items", "evidence_presentations", "task_outcome_links", "attribute_change_logs", "weekly_reviews", "path_adjustments"}
