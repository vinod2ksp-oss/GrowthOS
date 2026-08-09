import importlib
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.db import session as session_module


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phase3.sqlite3'}")
    monkeypatch.setenv("JWT_SECRET", "phase3-secret")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    importlib.reload(session_module)
    import app.main as main_module
    importlib.reload(main_module)
    from app.db.base import Base
    Base.metadata.create_all(bind=session_module.engine)
    with TestClient(main_module.app) as test_client: yield test_client


def user(client: TestClient, email: str) -> dict[str, str]:
    assert client.post("/api/v1/register", json={"email": email, "password": "secret123"}).status_code == 200
    token = client.post("/api/v1/login", json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def task(client: TestClient, headers: dict[str, str], title: str, minutes: int = 60) -> str:
    response = client.post("/api/v1/tasks", headers=headers, json={"title": title, "task_type": "main", "status": "pending", "estimated_minutes": minutes, "completion_standard": "User-provided completion", "evidence_requirements": "Result and test"})
    assert response.status_code == 200
    return response.json()["id"]


def evidence(client: TestClient, headers: dict[str, str], task_id: str, kind: str) -> None:
    response = client.post("/api/v1/evidences", headers=headers, data={"task_id": task_id, "evidence_type": kind}, files={"file": (f"{kind}.txt", kind.encode(), "text/plain")})
    assert response.status_code == 200


def complete_and_evaluate(client: TestClient, headers: dict[str, str], task_id: str) -> str:
    evidence(client, headers, task_id, "result"); evidence(client, headers, task_id, "test")
    assert client.patch(f"/api/v1/tasks/{task_id}", headers=headers, json={"status": "done"}).status_code == 200
    result = client.post(f"/api/v1/tasks/{task_id}/evaluations", headers=headers)
    assert result.status_code == 201 and result.json()["status"] == "completed"
    return result.json()["id"]


def test_effective_outcome_inventory_idempotency_and_isolation(client: TestClient) -> None:
    a, b = user(client, "outcome-a@example.com"), user(client, "outcome-b@example.com")
    task_id = task(client, a, "User completed project task")
    complete_and_evaluate(client, a, task_id)
    first = client.post(f"/api/v1/tasks/{task_id}/outcome", headers=a, json={"outcome_type": "project_result", "attribute_key": "programming_tools"})
    second = client.post(f"/api/v1/tasks/{task_id}/outcome", headers=a, json={"outcome_type": "project_result", "attribute_key": "programming_tools"})
    assert first.status_code == 201 and second.status_code == 201 and first.json()["id"] == second.json()["id"]
    inventory = client.get("/api/v1/inventory", headers=a).json()
    assert len(inventory) == 1 and inventory[0]["task_id"] == task_id and inventory[0]["attribute_keys"] == ["programming_tools"]
    assert client.get("/api/v1/inventory", headers=b).json() == []
    assert client.get(f"/api/v1/inventory/{inventory[0]['id']}", headers=b).status_code == 404
    goal = client.post("/api/v1/goals", headers=a, json={"target_major": "User inventory target"}).json()
    client.post(f"/api/v1/goals/{goal['id']}/requirements", headers=a, json={"category": "programming_tools", "title": "User inventory requirement", "metric_type": "qualitative", "source_type": "user_input", "verification_status": "confirmed"})
    assert len(client.get(f"/api/v1/inventory?goal_id={goal['id']}&relevant_only=true", headers=a).json()) == 1
    assert client.patch(f"/api/v1/inventory/{inventory[0]['id']}", headers=a, json={"user_note": "User note", "hidden_from_current_goal": True}).status_code == 204
    assert client.get("/api/v1/inventory", headers=a).json()[0]["user_note"] == "User note"


def test_timing_only_creates_no_outcome_and_diagnostic_only_changes_confidence(client: TestClient) -> None:
    headers = user(client, "diagnostic@example.com")
    timed = task(client, headers, "Timing only")
    started = client.post("/api/v1/timers/start", headers=headers, json={"task_id": timed}).json()
    client.post(f"/api/v1/timers/{started['id']}/end", headers=headers)
    client.patch(f"/api/v1/tasks/{timed}", headers=headers, json={"status": "done"})
    client.post(f"/api/v1/tasks/{timed}/evaluations", headers=headers)
    assert client.post(f"/api/v1/tasks/{timed}/outcome", headers=headers, json={"outcome_type": "task_result", "attribute_key": "english"}).status_code == 409
    assert client.get("/api/v1/inventory", headers=headers).json() == []

    diagnostic = task(client, headers, "User diagnostic task")
    complete_and_evaluate(client, headers, diagnostic)
    before = next(x for x in client.get("/api/v1/growth-attributes", headers=headers).json() if x["attribute_key"] == "english")
    created = client.post(f"/api/v1/tasks/{diagnostic}/outcome", headers=headers, json={"outcome_type": "diagnostic_completed", "attribute_key": "english"})
    assert created.status_code == 201
    after = next(x for x in client.get("/api/v1/growth-attributes", headers=headers).json() if x["attribute_key"] == "english")
    assert before["range_min"] is None and after["range_min"] is None
    assert after["confidence"] > before["confidence"]
    changes = client.get("/api/v1/attribute-changes", headers=headers).json()
    assert any(row["source_type"] == "diagnostic_completed" and row["source_id"] == created.json()["id"] for row in changes)


def test_evidence_rejection_is_traceable(client: TestClient) -> None:
    headers = user(client, "reject@example.com")
    uploaded = client.post("/api/v1/materials", headers=headers, data={"material_type": "transcript"}, files={"file": ("grade.png", b"image", "image/png")}).json()
    confirmed = client.post(f"/api/v1/materials/{uploaded['id']}/confirm", headers=headers, json={"courses": [{"course_name": "User course", "course_category": "mathematical_foundation", "score": 90, "full_score": 100}], "experiences": []}).json()[0]
    client.get("/api/v1/growth-attributes", headers=headers)
    rejected = client.post(f"/api/v1/growth-evidences/{confirmed['id']}/reject", headers=headers)
    assert rejected.status_code == 200 and rejected.json()["verification_status"] == "rejected"
    attribute = next(x for x in client.get("/api/v1/growth-attributes", headers=headers).json() if x["attribute_key"] == "mathematical_foundation")
    assert attribute["range_min"] is None
    assert any(row["source_type"] == "evidence_rejected" for row in client.get("/api/v1/attribute-changes", headers=headers).json())


def test_weekly_review_progress_adjustment_plan_and_user_isolation(client: TestClient) -> None:
    a, b = user(client, "review-a@example.com"), user(client, "review-b@example.com")
    client.put("/api/v1/profile", headers=a, json={"nickname": "A", "weekly_study_hours": 2})
    goal = client.post("/api/v1/goals", headers=a, json={"target_major": "User target"}).json()
    pending = task(client, a, "Unfinished user task", 90)
    monday = date.today() - timedelta(days=date.today().weekday())
    payload = {"period_start": monday.isoformat(), "goal_id": goal["id"]}
    first = client.post("/api/v1/weekly-reviews", headers=a, json=payload)
    second = client.post("/api/v1/weekly-reviews", headers=a, json=payload)
    assert first.status_code == 201 and first.json()["id"] == second.json()["id"]
    assert len([item for item in client.get("/api/v1/inventory", headers=a).json() if item["source"] == "system_report"]) == 1
    assert first.json()["progress_json"]["progress_value"] is None
    assert client.get("/api/v1/weekly-reviews", headers=b).json() == []
    adjustments = client.post(f"/api/v1/weekly-reviews/{first.json()['id']}/adjustments", headers=a).json()
    assert adjustments and all(row["status"] == "pending" and row["requires_user_confirmation"] for row in adjustments)
    before = client.get(f"/api/v1/tasks/{pending}", headers=a).json()["estimated_minutes"]
    target = next((row for row in adjustments if row["target_task_id"]), None)
    if target:
        assert client.get(f"/api/v1/tasks/{pending}", headers=a).json()["estimated_minutes"] == before
        client.post(f"/api/v1/path-adjustments/{target['id']}/confirm", headers=a)
    plan = client.post(f"/api/v1/weekly-plans?goal_id={goal['id']}&review_id={first.json()['id']}", headers=a).json()
    assert sum(item["estimated_minutes"] for item in plan["items"]) <= 120
    assert any(item["source_key"] == f"continue:{pending}" for item in plan["items"])
    editable = plan["items"][0]
    assert client.patch(f"/api/v1/weekly-plans/{plan['id']}/items/{editable['id']}", headers=a, json={"estimated_minutes": 45}).status_code == 200
    assert client.post(f"/api/v1/weekly-plans/{plan['id']}/items/{editable['id']}/delay", headers=a).status_code == 200
    assert client.delete(f"/api/v1/weekly-plans/{plan['id']}/items/{editable['id']}", headers=a).status_code == 204
    regenerated = client.post(f"/api/v1/weekly-plans/{plan['id']}/regenerate", headers=a)
    assert regenerated.status_code == 201 and regenerated.json()["regeneration_count"] == 1
    assert client.post(f"/api/v1/weekly-plans/{regenerated.json()['id']}/regenerate", headers=a).status_code == 409
    duplicate = client.post(f"/api/v1/weekly-plans?goal_id={goal['id']}&review_id={first.json()['id']}", headers=a).json()
    assert not {item["source_key"] for item in regenerated.json()["items"]} & {item["source_key"] for item in duplicate["items"]}
    assert client.get("/api/v1/inventory", headers=b).json() == []
