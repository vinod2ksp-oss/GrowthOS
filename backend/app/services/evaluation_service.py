from typing import Any

from app.models.task import Evidence, LearningSession


def evaluate_task(task: Any, sessions: list[LearningSession], evidences: list[Evidence]) -> dict[str, str]:
    has_timing = any(session.elapsed_seconds > 0 or session.is_running for session in sessions)
    has_result_evidence = any(evidence.evidence_type in {"result", "application"} for evidence in evidences)
    has_test_evidence = any(evidence.evidence_type == "test" for evidence in evidences)

    if not has_timing and not evidences:
        return {"status": "need_more_evidence", "reason": "暂未发现有效投入或成果证据，请补充学习记录与成果。"}
    if has_timing and not evidences:
        return {"status": "in_progress", "reason": "仅有计时记录，说明已投入，但尚未上传成果证据。"}
    if has_timing and evidences and not has_test_evidence:
        return {"status": "partial_complete", "reason": "已有计时记录和成果证据，可判断为部分完成。"}
    if has_result_evidence and has_test_evidence:
        return {"status": "completed", "reason": "已有成果与测试证据，满足完成标准。"}
    return {"status": "need_more_evidence", "reason": "证据不足，建议补充结果或测试附件。"}
