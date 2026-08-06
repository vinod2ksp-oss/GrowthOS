from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.growth import AttributeEvidenceLink, GrowthAttribute, GrowthEvidence
from app.models.task import LearningSession, Task

ATTRIBUTE_KEYS = ["mathematical_foundation", "english", "professional_knowledge", "academic_research", "data_analysis", "practical_experience", "programming_tools", "communication", "task_execution", "learning_stability"]


class GrowthDiagnosisService:
    def diagnose(self, db: Session, user_id: str) -> list[dict]:
        evidences = db.execute(select(GrowthEvidence).where(GrowthEvidence.user_id == user_id, GrowthEvidence.verification_status.in_(["user_confirmed", "system_verified"]))).scalars().all()
        result = []
        for key in ATTRIBUTE_KEYS:
            linked = [e for e in evidences if self._supports(e, key)]
            ratios = [e.metadata_json["score"] / e.metadata_json["full_score"] for e in linked if e.evidence_type == "course_grade" and e.metadata_json and e.metadata_json.get("course_category") == key and e.metadata_json.get("full_score", 0) > 0]
            status, low, high, explanation = self._assessment(key, linked, ratios, db, user_id)
            confidence = min(1.0, len(linked) * 0.2 + len(ratios) * 0.15)
            attribute = db.execute(select(GrowthAttribute).where(GrowthAttribute.user_id == user_id, GrowthAttribute.attribute_key == key)).scalar_one_or_none()
            if attribute is None:
                attribute = GrowthAttribute(user_id=user_id, attribute_key=key, explanation=explanation)
                db.add(attribute); db.flush()
            attribute.current_status, attribute.range_min, attribute.range_max = status, low, high
            attribute.confidence, attribute.explanation = confidence, explanation
            db.execute(delete(AttributeEvidenceLink).where(AttributeEvidenceLink.attribute_id == attribute.id))
            for evidence in linked:
                db.add(AttributeEvidenceLink(attribute_id=attribute.id, evidence_id=evidence.id))
            result.append({"attribute_key": key, "current_status": status, "range_min": low, "range_max": high, "confidence": confidence, "evidence_count": len(linked), "evidence_ids": [e.id for e in linked], "explanation": explanation, "gap_status": attribute.gap_status})
        db.commit()
        return result

    def _supports(self, evidence: GrowthEvidence, key: str) -> bool:
        meta = evidence.metadata_json or {}
        if evidence.evidence_type == "course_grade":
            return meta.get("course_category") == key
        return key in meta.get("associated_skills", [])

    def _assessment(self, key: str, linked: list[GrowthEvidence], ratios: list[float], db: Session, user_id: str) -> tuple:
        if key in {"task_execution", "learning_stability"}:
            task_count = db.scalar(select(func.count(Task.id)).where(Task.user_id == user_id)) or 0
            sessions = db.execute(select(LearningSession).where(LearningSession.user_id == user_id)).scalars().all()
            completed = db.scalar(select(func.count(Task.id)).where(Task.user_id == user_id, Task.status == "done")) or 0
            if not task_count or not sessions:
                return "insufficient_evidence", None, None, "缺少真实任务或学习会话，不能从材料推测该能力。"
            status = "stable" if completed and len(sessions) >= 3 else "developing"
            return status, None, None, f"依据 {task_count} 个真实任务、{completed} 个已完成任务和 {len(sessions)} 条学习会话进行定性判断。"
        if ratios:
            low, high = min(ratios), max(ratios)
            status = "strong" if low >= .85 and len(ratios) >= 2 else "stable" if low >= .7 else "developing"
            return status, low, high, f"依据 {len(ratios)} 门用户确认课程的原始成绩比例区间，不将不同课程合并为精确分数。"
        if linked:
            return ("developing" if len(linked) >= 2 else "emerging"), None, None, f"存在 {len(linked)} 条用户确认的定性证据；证据不包含可比较分值，因此不显示数值区间。"
        return "insufficient_evidence", None, None, "尚无用户确认且可关联到该维度的证据。"
