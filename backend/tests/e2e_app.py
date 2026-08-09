from app.main import app
from app.services.ai_service import AIService, LLMResult, get_ai_service
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User


class E2EFakeProvider:
    enabled = True
    model = "e2e-fake-model"

    def generate_json(self, system_prompt: str, user_payload: dict, timeout: float) -> LLMResult:
        if "material_type" in user_payload:
            data = {
                "courses": [{"course_name": "E2E user course", "course_category": "mathematical_foundation", "score": 84, "full_score": 100}],
                "experiences": [],
                "missing_information": ["semester"],
            }
        elif "rule_diagnosis" in user_payload:
            data = {"explanation": "The rule diagnosis is supported by confirmed user evidence.", "key_evidence_ids": user_payload["rule_diagnosis"].get("evidence_ids", []), "low_confidence_reasons": [], "needed_evidence": [], "priority_improvement": "Continue collecting verified evidence"}
        elif "supplied_text" in user_payload:
            data = {"requirements": [{"category": "mathematical_foundation", "title": "E2E supplied requirement", "metric_type": "ratio", "target_min": 0.9, "source_type": "user_input", "verification_status": "pending"}], "time_nodes": [], "missing_information": [], "relationship_explanation": "Organized only from the supplied text."}
        elif "items" in user_payload:
            data = {"items": [{"id": item["id"], "title": f"AI refined {item['title']}", "completion_standard": "Submit a verifiable result", "evidence_requirements": "Attach result and test evidence", "generation_reason": "Addresses the existing confirmed gap"} for item in user_payload["items"]]}
        elif "rule_evaluation" in user_payload:
            data = {"summary": "Feedback grounded in the rule evaluation.", "strengths": ["Submitted verifiable evidence"], "incomplete_parts": [], "suggestions": ["Keep the evidence linked to the task"], "followup_questions": []}
        elif "title" in user_payload:
            data = {"questions": ["What did you verify in this task?"]}
        else:
            data = {"evaluation": "The answer was reviewed as auxiliary feedback."}
        return LLMResult(data, input_tokens=10, output_tokens=10)


app.dependency_overrides[get_ai_service] = lambda: AIService(E2EFakeProvider())


class TestPromotion(BaseModel):
    email: str


@app.post("/api/v1/test/promote-admin", include_in_schema=False)
def promote_test_admin(payload: TestPromotion, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if user is None:
        raise HTTPException(404, "test user not found")
    user.role = "admin"; db.commit()
    return {"role": "admin"}
