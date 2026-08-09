import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db import session as session_module
from app.models.user import User


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phase5.sqlite3'}")
    monkeypatch.setenv("JWT_SECRET", "phase5-secret")
    monkeypatch.delenv("AI_API_KEY", raising=False)
    importlib.reload(session_module)
    import app.main as main_module
    importlib.reload(main_module)
    from app.db.base import Base
    Base.metadata.create_all(bind=session_module.engine)
    with TestClient(main_module.app) as value:
        yield value


def user(client: TestClient, email: str) -> dict[str, str]:
    assert client.post("/api/v1/register", json={"email": email, "password": "secret123"}).status_code == 200
    token = client.post("/api/v1/login", json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def promote(email: str) -> None:
    with session_module.SessionLocal() as db:
        row = db.execute(select(User).where(User.email == email)).scalar_one()
        row.role = "admin"; db.commit()


def resource_payload(name: str, **overrides) -> dict:
    payload = {"name": name, "product_type": "physical_book", "description": "Administrator supplied description", "provider_name": "Test provider", "price": 50, "currency": "CNY", "is_free": False, "external_url": "https://example.com/resource", "applicable_stages": ["preparation"], "related_attributes": ["mathematical_foundation"], "related_task_tags": ["algebra"], "applicable_goal_types": ["preparation"], "content_year": 2026, "is_required": False, "is_sponsored": False, "source_type": "admin_entry", "copyright_status": "verified", "status": "active"}
    payload.update(overrides); return payload


def create(client: TestClient, admin: dict[str, str], name: str, **overrides) -> dict:
    response = client.post("/api/v1/admin/resources", headers=admin, json=resource_payload(name, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_empty_marketplace_and_admin_permissions(client: TestClient) -> None:
    regular = user(client, "regular-market@example.com")
    assert client.get("/api/v1/resources", headers=regular).json() == []
    assert client.post("/api/v1/admin/resources", headers=regular, json=resource_payload("Forbidden")).status_code == 403
    promote("regular-market@example.com")
    created = create(client, regular, "Admin entered resource", status="draft")
    assert created["status"] == "draft" and client.get("/api/v1/resources", headers=regular).json() == []
    activated = client.patch(f"/api/v1/admin/resources/{created['id']}", headers=regular, json={"status": "active"})
    assert activated.status_code == 200
    assert len(client.get("/api/v1/resources", headers=regular).json()) == 1
    assert client.patch(f"/api/v1/admin/resources/{created['id']}", headers=regular, json={"status": "inactive"}).status_code == 200
    assert client.get("/api/v1/resources", headers=regular).json() == []
    rejected = client.post("/api/v1/admin/resources", headers=regular, json=resource_payload("Unknown copyright", product_type="digital_material", copyright_status="unknown"))
    assert rejected.status_code == 422


def test_rule_recommendations_free_alternatives_sponsorship_and_owned(client: TestClient) -> None:
    admin = user(client, "admin-rec@example.com"); promote("admin-rec@example.com")
    learner = user(client, "learner-rec@example.com")
    free = create(client, admin, "Free alternative", product_type="free_resource", price=0, is_free=True)
    natural = create(client, admin, "Natural match", free_alternative_ids=[free["id"]])
    sponsored = create(client, admin, "Sponsored match", is_sponsored=True, sponsorship_label="Promoted")
    create(client, admin, "Inactive match", status="inactive")
    create(client, admin, "Outdated match", status="outdated")
    client.put("/api/v1/profile", headers=learner, json={"nickname": "Learner", "learning_stage": "preparation", "resource_budget": 60})
    goal = client.post("/api/v1/goals", headers=learner, json={"target_major": "User target", "current_stage": "preparation"}).json()
    client.post(f"/api/v1/goals/{goal['id']}/requirements", headers=learner, json={"category": "mathematical_foundation", "title": "User mathematics requirement", "metric_type": "ratio", "target_min": .9, "source_type": "user_input", "verification_status": "confirmed"})
    task = client.post("/api/v1/tasks", headers=learner, json={"title": "Practice algebra", "task_type": "main", "status": "pending"}).json()
    recommendations = client.get("/api/v1/resource-recommendations", headers=learner).json()
    by_id = {item["resource_id"]: item for item in recommendations}
    assert natural["id"] in by_id and sponsored["id"] in by_id
    assert by_id[natural["id"]]["related_task"] == task["title"]
    assert by_id[natural["id"]]["related_gap"] == "User mathematics requirement"
    assert by_id[natural["id"]]["free_alternative_ids"] == [free["id"]]
    assert by_id[natural["id"]]["relevance_score"] == by_id[sponsored["id"]]["relevance_score"]
    assert by_id[sponsored["id"]]["sponsored"] is True
    assert all(item["name"] not in {"Inactive match", "Outdated match"} for item in recommendations)
    owned = client.post("/api/v1/owned-resources", headers=learner, json={"custom_name": "My existing book", "resource_type": "physical_book", "status": "owned"})
    assert owned.status_code == 201
    updated = {item["resource_id"]: item for item in client.get("/api/v1/resource-recommendations", headers=learner).json()}
    assert updated[natural["id"]]["already_owned_similar"] is True and updated[natural["id"]]["warnings"]
    task_resources = client.get(f"/api/v1/tasks/{task['id']}/resources", headers=learner).json()
    assert 0 < len(task_resources) <= 3 and all(item["related_task"] == task["title"] for item in task_resources)
    unrelated_task = client.post("/api/v1/tasks", headers=learner, json={"title": "Completely unrelated task", "task_type": "support", "status": "pending"}).json()
    assert client.get(f"/api/v1/tasks/{unrelated_task['id']}/resources", headers=learner).json() == []


def test_interactions_are_isolated_and_do_not_change_task_or_attribute(client: TestClient) -> None:
    admin = user(client, "admin-actions@example.com"); promote("admin-actions@example.com")
    a = user(client, "actions-a@example.com"); b = user(client, "actions-b@example.com")
    product = create(client, admin, "Action resource")
    task = client.post("/api/v1/tasks", headers=a, json={"title": "Practice algebra", "task_type": "main", "status": "pending"}).json()
    before_attribute = next(item for item in client.get("/api/v1/growth-attributes", headers=a).json() if item["attribute_key"] == "mathematical_foundation")
    assert client.put(f"/api/v1/resources/{product['id']}/favorite", headers=a).status_code == 204
    assert len(client.get("/api/v1/resource-favorites", headers=a).json()) == 1
    assert client.get("/api/v1/resource-favorites", headers=b).json() == []
    assert client.post("/api/v1/owned-resources", headers=a, json={"resource_product_id": product["id"], "resource_type": "physical_book"}).status_code == 201
    assert client.get("/api/v1/owned-resources", headers=b).json() == []
    clicked = client.post(f"/api/v1/resources/{product['id']}/interactions", headers=a, json={"interaction_type": "external_clicked"})
    assert clicked.status_code == 201 and clicked.json()["external_url"] == "https://example.com/resource"
    assert client.post(f"/api/v1/resources/{product['id']}/interactions", headers=a, json={"interaction_type": "used_for_task", "task_id": task["id"]}).status_code == 201
    after_task = client.get(f"/api/v1/tasks/{task['id']}", headers=a).json()
    after_attribute = next(item for item in client.get("/api/v1/growth-attributes", headers=a).json() if item["attribute_key"] == "mathematical_foundation")
    assert after_task["status"] == "pending"
    assert (after_attribute["current_status"], after_attribute["range_min"], after_attribute["confidence"]) == (before_attribute["current_status"], before_attribute["range_min"], before_attribute["confidence"])
    assert client.post(f"/api/v1/resources/{product['id']}/interactions", headers=a, json={"interaction_type": "dismissed"}).status_code == 201
    assert all(item["resource_id"] != product["id"] for item in client.get("/api/v1/resource-recommendations", headers=a).json())


def test_no_ai_key_keeps_rule_recommendations(client: TestClient) -> None:
    admin = user(client, "admin-no-ai@example.com"); promote("admin-no-ai@example.com")
    learner = user(client, "learner-no-ai@example.com")
    product = create(client, admin, "Rule only resource")
    client.post("/api/v1/tasks", headers=learner, json={"title": "Practice algebra", "task_type": "main", "status": "pending"})
    response = client.post("/api/v1/resource-recommendations/ai-explain", headers=learner)
    assert response.status_code == 200 and response.json()["status"] == "rules_only"
    assert response.json()["items"][0]["resource_id"] == product["id"]


def test_ai_provider_failure_keeps_rule_order(client: TestClient) -> None:
    from app.services.ai_service import AIService, get_ai_service
    import app.main as main_module

    class FailingProvider:
        enabled = True
        model = "failing-test-provider"
        def generate_json(self, system_prompt, user_payload, timeout):
            raise TimeoutError("test timeout")

    admin = user(client, "admin-ai-failure@example.com"); promote("admin-ai-failure@example.com")
    learner = user(client, "learner-ai-failure@example.com")
    product = create(client, admin, "Failure fallback resource")
    client.post("/api/v1/tasks", headers=learner, json={"title": "Practice algebra", "task_type": "main", "status": "pending"})
    expected = client.get("/api/v1/resource-recommendations", headers=learner).json()
    main_module.app.dependency_overrides[get_ai_service] = lambda: AIService(FailingProvider())
    try:
        response = client.post("/api/v1/resource-recommendations/ai-explain", headers=learner)
    finally:
        main_module.app.dependency_overrides.pop(get_ai_service, None)
    assert response.status_code == 200 and response.json()["status"] == "rules_only"
    assert [item["resource_id"] for item in response.json()["items"]] == [item["resource_id"] for item in expected] == [product["id"]]
