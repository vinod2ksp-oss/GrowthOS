from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.goal import StudyGoal
from app.models.growth import GoalRequirement
from app.services.growth_diagnosis_service import GrowthDiagnosisService


class GoalGapAnalysisService:
    def analyze(self, db: Session, user_id: str, goal_id: str) -> list[dict]:
        goal = db.execute(select(StudyGoal).where(StudyGoal.id == goal_id, StudyGoal.user_id == user_id)).scalar_one_or_none()
        if goal is None:
            raise LookupError("目标不存在")
        attributes = {item["attribute_key"]: item for item in GrowthDiagnosisService().diagnose(db, user_id)}
        requirements = db.execute(select(GoalRequirement).where(GoalRequirement.goal_id == goal_id)).scalars().all()
        output = []
        for requirement in requirements:
            current = attributes.get(requirement.category)
            level, missing, next_step = "unknown", [], "补充或确认相关证据后重新分析。"
            if requirement.verification_status != "confirmed":
                missing.append("目标要求尚未确认")
            elif not current or current["current_status"] == "insufficient_evidence":
                missing.append("个人能力证据不足")
            elif requirement.target_min is not None and current["range_min"] is not None:
                delta = requirement.target_min - current["range_min"]
                level = "no_gap" if delta <= 0 else "minor" if delta <= .1 else "moderate" if delta <= .25 else "major"
                next_step = "保持当前证据和学习投入。" if level == "no_gap" else "围绕该要求安排可验证的提升任务。"
            else:
                missing.append("缺少可比较的量化区间")
            output.append({"requirement_id": requirement.id, "title": requirement.title, "category": requirement.category, "current_evidence": current["evidence_ids"] if current else [], "current_status": current["current_status"] if current else "insufficient_evidence", "current_range": [current["range_min"], current["range_max"]] if current and current["range_min"] is not None else None, "target": {"min": requirement.target_min, "max": requirement.target_max, "unit": requirement.unit}, "gap_level": level, "confidence": current["confidence"] if current else 0, "missing_evidence": missing, "next_step": next_step})
        return output
