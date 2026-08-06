import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.db import session as session_module


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phase2.sqlite3'}")
    monkeypatch.setenv("JWT_SECRET", "phase2-secret")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    importlib.reload(session_module)
    import app.main as main_module
    importlib.reload(main_module)
    from app.db.base import Base
    Base.metadata.create_all(bind=session_module.engine)
    with TestClient(main_module.app) as test_client:
        yield test_client


def create_user(client: TestClient, email: str) -> dict[str, str]:
    assert client.post("/api/v1/register", json={"email": email, "password": "secret123"}).status_code == 200
    response = client.post("/api/v1/login", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def upload(client: TestClient, headers: dict[str, str], name: str = "grade.png") -> dict:
    response = client.post("/api/v1/materials", headers=headers, data={"material_type": "transcript"}, files={"file": (name, b"real-user-file", "image/png")})
    assert response.status_code == 201, response.text
    return response.json()


def test_material_security_parsing_failure_and_isolation(client: TestClient) -> None:
    a, b = create_user(client, "material-a@example.com"), create_user(client, "material-b@example.com")
    rejected = client.post("/api/v1/materials", headers=a, data={"material_type": "other"}, files={"file": ("unsafe.exe", b"x", "application/octet-stream")})
    assert rejected.status_code == 400
    material = upload(client, a)
    assert material["parse_status"] == "pending_confirmation"
    assert material["stored_filename"] != material["original_filename"]
    assert client.get(f"/api/v1/materials/{material['id']}", headers=b).status_code == 404
    assert client.delete(f"/api/v1/materials/{material['id']}", headers=b).status_code == 404
    broken_pdf = client.post("/api/v1/materials", headers=a, data={"material_type": "resume"}, files={"file": ("broken.pdf", b"not-pdf", "application/pdf")})
    assert broken_pdf.status_code == 201 and broken_pdf.json()["parse_status"] == "parse_failed"


def test_confirmation_is_idempotent_and_course_diagnosis_is_explainable(client: TestClient) -> None:
    headers = create_user(client, "evidence@example.com")
    material = upload(client, headers)
    payload = {"courses": [{"course_name": "User supplied course", "course_category": "mathematical_foundation", "score": 82, "full_score": 100, "credit": 4, "semester": "2026", "is_core": True}], "experiences": []}
    first = client.post(f"/api/v1/materials/{material['id']}/confirm", headers=headers, json=payload)
    second = client.post(f"/api/v1/materials/{material['id']}/confirm", headers=headers, json=payload)
    assert first.status_code == 200 and second.status_code == 200
    assert len(first.json()) == len(second.json()) == 1
    evidences = client.get("/api/v1/growth-evidences", headers=headers).json()
    assert len(evidences) == 1 and evidences[0]["verification_status"] == "user_confirmed"
    attributes = {item["attribute_key"]: item for item in client.get("/api/v1/growth-attributes", headers=headers).json()}
    math = attributes["mathematical_foundation"]
    assert math["range_min"] == pytest.approx(.82) and math["range_max"] == pytest.approx(.82)
    assert math["evidence_ids"] == [evidences[0]["id"]] and math["explanation"]
    assert attributes["english"]["range_min"] is None
    assert attributes["english"]["current_status"] == "insufficient_evidence"
    assert attributes["task_execution"]["current_status"] == "insufficient_evidence"


def test_requirement_crud_isolation_and_unknown_gap(client: TestClient) -> None:
    a, b = create_user(client, "goal-a@example.com"), create_user(client, "goal-b@example.com")
    goal = client.post("/api/v1/goals", headers=a, json={"target_major": "User target", "target_year": 2028}).json()
    requirement = client.post(f"/api/v1/goals/{goal['id']}/requirements", headers=a, json={"category": "english", "title": "User entered English requirement", "metric_type": "score", "target_min": 80, "unit": "points", "source_type": "user_input", "verification_status": "pending"})
    assert requirement.status_code == 201
    requirement_id = requirement.json()["id"]
    assert client.get(f"/api/v1/goals/{goal['id']}/requirements", headers=b).status_code == 404
    gaps = client.get(f"/api/v1/goals/{goal['id']}/gaps", headers=a).json()
    assert gaps[0]["gap_level"] == "unknown" and "目标要求尚未确认" in gaps[0]["missing_evidence"]
    updated = client.patch(f"/api/v1/goals/{goal['id']}/requirements/{requirement_id}", headers=a, json={"verification_status": "confirmed"})
    assert updated.status_code == 200
    confirmed_gap = client.get(f"/api/v1/goals/{goal['id']}/gaps", headers=a).json()[0]
    assert confirmed_gap["gap_level"] == "unknown" and "个人能力证据不足" in confirmed_gap["missing_evidence"]
    attribute_response = client.get(f"/api/v1/growth-attributes?goal_id={goal['id']}", headers=a)
    assert attribute_response.status_code == 200, attribute_response.text
    assert next(item for item in attribute_response.json() if item["attribute_key"] == "english")["gap_status"] == "unknown"
    assert client.delete(f"/api/v1/goals/{goal['id']}/requirements/{requirement_id}", headers=a).status_code == 204


def test_weekly_plan_budget_deduplication_and_confirmation(client: TestClient) -> None:
    headers = create_user(client, "planner@example.com")
    client.put("/api/v1/profile", headers=headers, json={"nickname": "Planner", "weekly_study_hours": 2})
    goal = client.post("/api/v1/goals", headers=headers, json={"target_major": "User target"}).json()
    client.post(f"/api/v1/goals/{goal['id']}/requirements", headers=headers, json={"category": "programming_tools", "title": "User coding requirement", "metric_type": "qualitative", "source_type": "user_input", "verification_status": "confirmed"})
    plan = client.post(f"/api/v1/weekly-plans?goal_id={goal['id']}", headers=headers)
    assert plan.status_code == 201 and plan.json()["status"] == "draft"
    items = plan.json()["items"]
    assert sum(item["estimated_minutes"] for item in items) <= 120
    assert sum(item["task_type"] == "main" for item in items) <= 1
    assert client.get("/api/v1/tasks", headers=headers).json() == []
    confirmed = client.post(f"/api/v1/weekly-plans/{plan.json()['id']}/confirm", headers=headers, json={"accepted_item_ids": [item["id"] for item in items]})
    assert confirmed.status_code == 200 and confirmed.json()["status"] == "confirmed"
    tasks = client.get("/api/v1/tasks", headers=headers).json()
    assert len(tasks) == len(items)
    assert client.post(f"/api/v1/weekly-plans/{plan.json()['id']}/confirm", headers=headers, json={}).status_code == 200
    assert len(client.get("/api/v1/tasks", headers=headers).json()) == len(tasks)
    second = client.post(f"/api/v1/weekly-plans?goal_id={goal['id']}", headers=headers).json()
    assert all(item["title"] not in {task["title"] for task in tasks} for item in second["items"])
