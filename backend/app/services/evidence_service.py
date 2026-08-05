from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Evidence, Task
from app.schemas.evidence import EvidenceRead
from app.services.storage_service import StorageService


def list_evidences(db: Session, user_id: str) -> list[EvidenceRead]:
    evidences = db.execute(select(Evidence).where(Evidence.user_id == user_id)).scalars().all()
    return [EvidenceRead.model_validate(item) for item in evidences]


def save_upload(db: Session, file: UploadFile, user_id: str, task_id: str | None, evidence_type: str, description: str | None) -> EvidenceRead:
    if task_id and db.execute(select(Task).where(Task.id == task_id, Task.user_id == user_id)).scalar_one_or_none() is None:
        raise ValueError("任务不存在")
    storage = StorageService()
    storage.validate(file)
    file_path, _ = storage.save(file)
    evidence = Evidence(
        user_id=user_id,
        task_id=task_id,
        evidence_type=evidence_type,
        description=description,
        file_name=file.filename,
        file_path=file_path,
        mime_type=file.content_type,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return EvidenceRead.model_validate(evidence)


def delete_evidence(db: Session, user_id: str, evidence_id: str) -> None:
    evidence = db.execute(select(Evidence).where(Evidence.id == evidence_id, Evidence.user_id == user_id)).scalar_one_or_none()
    if evidence is None:
        raise ValueError("证据不存在")
    if evidence.file_path:
        StorageService().remove(evidence.file_path)
    db.delete(evidence)
    db.commit()
