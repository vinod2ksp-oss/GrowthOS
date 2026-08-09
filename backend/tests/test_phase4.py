import importlib
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.db import session as session_module
from app.services.ai_service import AIService, LLMResult


class FakeProvider:
    enabled = True
    model = "test-fake-model"

    def __init__(self) -> None:
        self.response: dict | Exception = {}
        self.calls = 0

    def generate_json(self, system_prompt: str, user_payload: dict, timeout: float) -> LLMResult:
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        return LLMResult(self.response, input_tokens=11, output_tokens=7)


@pytest.fixture
def client_and_provider(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'phase4.sqlite3'}")
    monkeypatch.setenv("JWT_SECRET", "phase4-secret")
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.delenv("AI_API_KEY", raising=False)
    importlib.reload(session_module)
    import app.main as main_module

    importlib.reload(main_module)
    from app.db.base import Base
    from app.services.ai_service import get_ai_service

    Base.metadata.create_all(bind=session_module.engine)
    provider = FakeProvider()
    main_module.app.dependency_overrides[get_ai_service] = lambda: AIService(provider)
    with TestClient(main_module.app) as client:
        yield client, provider
    main_module.app.dependency_overrides.clear()


def user(client: TestClient, email: str) -> dict[str, str]:
    assert client.post("/api/v1/register", json={"email": email, "password": "secret123"}).status_code == 200
    token = client.post("/api/v1/login", json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()


def upload_docx(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/materials",
        headers=headers,
        data={"material_type": "transcript"},
        files={"file": ("user-transcript.docx", docx_bytes("User course 82/100"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 201, response.text
    assert response.json()["parse_status"] == "pending_confirmation"
    return response.json()


def test_no_key_and_provider_failure_degrade_without_formal_data(client_and_provider) -> None:
    client, provider = client_and_provider
    headers = user(client, "disabled-ai@example.com")
    goal = client.post("/api/v1/goals", headers=headers, json={"target_major": "User supplied target"})
    assert goal.status_code == 200

    provider.enabled = False
    settings = client.get("/api/v1/ai/settings", headers=headers).json()
    assert settings["enabled"] is False
    disabled = client.post(
        f"/api/v1/goals/{goal.json()['id']}/ai-organize",
        headers=headers,
        json={"supplied_text": "User supplied requirement"},
    )
    assert disabled.status_code == 200 and disabled.json()["analysis"] is None

    provider.enabled = True
    provider.response = TimeoutError("provider timeout")
    response = client.post(
        f"/api/v1/goals/{goal.json()['id']}/ai-organize",
        headers=headers,
        json={"supplied_text": "User supplied requirement"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "unavailable", "error_code": "provider_error", "analysis": None}
    assert client.get(f"/api/v1/goals/{goal.json()['id']}/requirements", headers=headers).json() == []


def test_invalid_ai_json_does_not_create_analysis_or_requirement(client_and_provider) -> None:
    client, provider = client_and_provider
    headers = user(client, "invalid-json@example.com")
    goal = client.post("/api/v1/goals", headers=headers, json={"target_major": "User target"}).json()
    provider.response = {"requirements": "not-a-list"}
    response = client.post(
        f"/api/v1/goals/{goal['id']}/ai-organize",
        headers=headers,
        json={"supplied_text": "Only user text"},
    )
    assert response.status_code == 200
    assert response.json()["error_code"] == "invalid_json"
    assert response.json()["analysis"] is None
    assert client.get(f"/api/v1/goals/{goal['id']}/requirements", headers=headers).json() == []


def test_material_ai_requires_consent_confirmation_and_user_isolation(client_and_provider) -> None:
    client, provider = client_and_provider
    owner = user(client, "material-ai-owner@example.com")
    other = user(client, "material-ai-other@example.com")
    material = upload_docx(client, owner)
    assert client.post(f"/api/v1/materials/{material['id']}/ai-parse", headers=owner).status_code == 403

    assert client.patch("/api/v1/ai/settings", headers=owner, json={"allow_material_analysis": True}).status_code == 200
    provider.response = {
        "courses": [{"course_name": "User course", "course_category": "mathematical_foundation", "score": 82, "full_score": 100}],
        "experiences": [],
        "missing_information": ["semester"],
    }
    draft = client.post(f"/api/v1/materials/{material['id']}/ai-parse", headers=owner)
    assert draft.status_code == 200 and draft.json()["status"] == "pending_confirmation"
    analysis_id = draft.json()["analysis"]["id"]
    assert client.get("/api/v1/growth-evidences", headers=owner).json() == []
    assert client.post(f"/api/v1/ai/analyses/{analysis_id}/confirm-material", headers=other).status_code == 404
    confirmed = client.post(f"/api/v1/ai/analyses/{analysis_id}/confirm-material", headers=owner)
    assert confirmed.status_code == 200 and len(confirmed.json()) == 1
    assert client.post(f"/api/v1/ai/analyses/{analysis_id}/confirm-material", headers=owner).status_code == 409
    assert client.get("/api/v1/growth-evidences", headers=other).json() == []


def test_ai_explanation_cannot_change_rule_attribute(client_and_provider) -> None:
    client, provider = client_and_provider
    headers = user(client, "attribute-ai@example.com")
    before = next(x for x in client.get("/api/v1/growth-attributes", headers=headers).json() if x["attribute_key"] == "english")
    provider.response = {
        "explanation": "Evidence is insufficient.",
        "key_evidence_ids": [],
        "low_confidence_reasons": ["No confirmed evidence"],
        "needed_evidence": ["A user-confirmed result"],
        "priority_improvement": "Add evidence",
    }
    response = client.post("/api/v1/growth-attributes/english/ai-explain", headers=headers)
    assert response.status_code == 200 and response.json()["status"] == "pending_confirmation"
    after = next(x for x in client.get("/api/v1/growth-attributes", headers=headers).json() if x["attribute_key"] == "english")
    assert (after["current_status"], after["range_min"], after["range_max"], after["confidence"]) == (
        before["current_status"], before["range_min"], before["range_max"], before["confidence"]
    )


def test_ai_plan_optimization_preserves_rule_constrained_items(client_and_provider) -> None:
    client, provider = client_and_provider
    headers = user(client, "plan-ai@example.com")
    client.put("/api/v1/profile", headers=headers, json={"nickname": "User", "weekly_study_hours": 2})
    goal = client.post("/api/v1/goals", headers=headers, json={"target_major": "User target"}).json()
    client.post(
        f"/api/v1/goals/{goal['id']}/requirements",
        headers=headers,
        json={"category": "english", "title": "User requirement", "metric_type": "qualitative", "source_type": "user_input", "verification_status": "confirmed"},
    )
    plan = client.post(f"/api/v1/weekly-plans?goal_id={goal['id']}", headers=headers).json()
    original = plan["items"]
    provider.response = {
        "items": [
            {"id": item["id"], "title": f"Refined {item['title']}", "completion_standard": "Verifiable completion", "evidence_requirements": "Attach a result", "generation_reason": "Tied to the existing gap"}
            for item in original
        ]
    }
    draft = client.post(f"/api/v1/weekly-plans/{plan['id']}/ai-optimize", headers=headers).json()
    assert draft["status"] == "pending_confirmation"
    provider.response = {"items": [{"id": "not-an-existing-item", "title": "Invalid", "completion_standard": "Invalid", "evidence_requirements": "Invalid", "generation_reason": "Invalid"}]}
    rejected = client.post(f"/api/v1/weekly-plans/{plan['id']}/ai-optimize", headers=headers)
    assert rejected.status_code == 200 and rejected.json()["error_code"] == "constraint_violation"
    confirmation = client.post(f"/api/v1/ai/analyses/{draft['analysis']['id']}/confirm-plan", headers=headers)
    assert confirmation.status_code == 200
    final_plan = client.post(f"/api/v1/weekly-plans/{plan['id']}/confirm", headers=headers, json={"accepted_item_ids": [x["id"] for x in original]}).json()
    assert sum(x["estimated_minutes"] for x in final_plan["items"]) <= 120
    assert len(final_plan["items"]) == len(original)


def test_goal_draft_confirmation_and_followups_are_user_scoped(client_and_provider) -> None:
    client, provider = client_and_provider
    owner = user(client, "goal-ai-owner@example.com")
    other = user(client, "goal-ai-other@example.com")
    goal = client.post("/api/v1/goals", headers=owner, json={"target_major": "User target"}).json()
    provider.response = {
        "requirements": [{"category": "english", "title": "Requirement from supplied text", "metric_type": "qualitative", "source_type": "user_input", "verification_status": "pending"}],
        "time_nodes": [], "missing_information": [], "relationship_explanation": "Based only on supplied text",
    }
    draft = client.post(f"/api/v1/goals/{goal['id']}/ai-organize", headers=owner, json={"supplied_text": "User text"}).json()["analysis"]
    assert client.post(f"/api/v1/ai/analyses/{draft['id']}/confirm-goal", headers=other).status_code == 404
    assert client.post(f"/api/v1/ai/analyses/{draft['id']}/confirm-goal", headers=owner).status_code == 200
    assert client.post(f"/api/v1/ai/analyses/{draft['id']}/confirm-goal", headers=owner).status_code == 409
    requirement = client.get(f"/api/v1/goals/{goal['id']}/requirements", headers=owner).json()
    assert len(requirement) == 1 and requirement[0]["source_type"] == "user_input"

    task = client.post("/api/v1/tasks", headers=owner, json={"title": "Diagnostic task", "task_type": "main", "status": "done"}).json()
    provider.response = {"questions": ["Explain the key idea"]}
    followup = client.post(f"/api/v1/tasks/{task['id']}/ai-followups", headers=owner).json()["items"][0]
    assert client.post(f"/api/v1/ai-followups/{followup['id']}/answer", headers=other, json={"answer": "Other answer"}).status_code == 404
    provider.response = {"evaluation": "The answer partially covers the idea."}
    answered = client.post(f"/api/v1/ai-followups/{followup['id']}/answer", headers=owner, json={"answer": "User answer"})
    assert answered.status_code == 200 and answered.json()["status"] == "evaluated"


def test_ai_feedback_cannot_override_rule_evaluation(client_and_provider) -> None:
    client, provider = client_and_provider
    headers = user(client, "feedback-ai@example.com")
    task = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "User task", "task_type": "main", "status": "pending", "completion_standard": "Submit result and test", "evidence_requirements": "result and test"},
    ).json()
    client.patch(f"/api/v1/tasks/{task['id']}", headers=headers, json={"status": "done"})
    evaluation = client.post(f"/api/v1/tasks/{task['id']}/evaluations", headers=headers).json()
    provider.response = {"summary": "Rule-grounded summary", "strengths": [], "incomplete_parts": ["Missing evidence"], "suggestions": ["Add evidence"], "followup_questions": []}
    feedback = client.post(f"/api/v1/tasks/{task['id']}/ai-feedback", headers=headers)
    assert feedback.status_code == 200
    assert feedback.json()["rule_status"] == evaluation["status"]
    latest = client.get(f"/api/v1/tasks/{task['id']}/evaluations/latest", headers=headers).json()
    assert latest["status"] == evaluation["status"]
