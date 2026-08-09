from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.growth import GrowthEvidence, TaskOutcomeLink
from app.models.task import Evidence, Task, TaskEvaluation
from app.services.growth_diagnosis_service import ATTRIBUTE_KEYS, GrowthDiagnosisService


class TaskOutcomeService:
    def convert(self, db: Session, user_id: str, task_id: str, outcome_type: str, attribute_key: str | None) -> GrowthEvidence:
        task = db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id)).scalar_one_or_none()
        if task is None: raise LookupError("任务不存在")
        if task.status != "done": raise ValueError("任务尚未完成")
        evaluation = db.execute(select(TaskEvaluation).where(TaskEvaluation.task_id == task_id, TaskEvaluation.user_id == user_id).order_by(TaskEvaluation.created_at.desc())).scalars().first()
        if evaluation is None or evaluation.status not in {"completed", "partial_complete"}: raise ValueError("任务尚无有效评测")
        existing = db.execute(select(TaskOutcomeLink).where(TaskOutcomeLink.task_id == task_id, TaskOutcomeLink.evaluation_id == evaluation.id)).scalar_one_or_none()
        if existing:
            return db.get(GrowthEvidence, existing.growth_evidence_id)
        source_evidences = db.execute(select(Evidence).where(Evidence.task_id == task_id, Evidence.user_id == user_id)).scalars().all()
        has_test = any(item.evidence_type == "test" for item in source_evidences)
        if not source_evidences: raise ValueError("仅有计时记录，不能生成成长成果")
        if attribute_key and attribute_key not in ATTRIBUTE_KEYS: raise ValueError("不支持的能力维度")
        if outcome_type == "learning_verified" and not has_test: raise ValueError("学习成果缺少测试证据")
        evidence_type = {"diagnostic_completed": "test_result", "learning_verified": "task_result", "mistake_archive": "portfolio", "project_result": "project"}.get(outcome_type, "task_result")
        metadata = {"task_id": task.id, "evaluation_id": evaluation.id, "source_evidence_ids": [item.id for item in source_evidences], "associated_skills": [attribute_key] if attribute_key else [], "confidence_only": outcome_type == "diagnostic_completed", "outcome_type": outcome_type}
        evidence = GrowthEvidence(user_id=user_id, source_key=f"task:{task.id}", evidence_type=evidence_type, title=task.title, description=f"由已完成任务及评测 {evaluation.status} 转化。", source_type="task", verification_status="system_verified", metadata_json=metadata)
        db.add(evidence); db.flush()
        db.add(TaskOutcomeLink(user_id=user_id, task_id=task.id, evaluation_id=evaluation.id, growth_evidence_id=evidence.id)); db.commit(); db.refresh(evidence)
        GrowthDiagnosisService().diagnose(db, user_id, outcome_type, evidence.id)
        return evidence
