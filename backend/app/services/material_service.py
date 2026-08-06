from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.growth import AttributeEvidenceLink, GrowthEvidence, Material
from app.schemas.growth import MaterialConfirmation
from app.services.material_parsing_service import MaterialParsingService

ALLOWED_SUFFIXES = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}
ALLOWED_TYPES = {"transcript", "resume", "course_grade", "research", "internship", "competition", "project", "certificate", "other"}


class MaterialService:
    def __init__(self) -> None:
        settings = get_settings()
        self.root = Path(settings.upload_dir).resolve() / "materials"
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_size = settings.max_upload_size

    def upload(self, db: Session, user_id: str, material_type: str, file: UploadFile) -> Material:
        if material_type not in ALLOWED_TYPES:
            raise ValueError("不支持的材料类型")
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise ValueError("不支持的文件类型")
        content = file.file.read(self.max_size + 1)
        if not content or len(content) > self.max_size:
            raise ValueError("文件为空或超过大小限制")
        stored = f"{uuid4().hex}{suffix}"
        destination = (self.root / stored).resolve()
        if self.root not in destination.parents:
            raise ValueError("非法文件路径")
        destination.write_bytes(content)
        parse_status, parsed = MaterialParsingService().parse(destination)
        material = Material(user_id=user_id, material_type=material_type, original_filename=Path(file.filename or "material").name, stored_filename=stored, mime_type=file.content_type or "application/octet-stream", file_size=len(content), storage_path=str(destination), parse_status=parse_status, parsed_content=parsed, confirmation_status="pending_confirmation")
        db.add(material); db.commit(); db.refresh(material)
        return material

    def confirm(self, db: Session, user_id: str, material_id: str, payload: MaterialConfirmation) -> list[GrowthEvidence]:
        material = db.execute(select(Material).where(Material.id == material_id, Material.user_id == user_id)).scalar_one_or_none()
        if material is None:
            raise LookupError("材料不存在")
        rows: list[tuple[str, str, str | None, dict, object]] = []
        for index, course in enumerate(payload.courses):
            rows.append((f"course:{index}", "course_grade", course.course_name, course.model_dump(mode="json"), None))
        for index, experience in enumerate(payload.experiences):
            rows.append((f"experience:{index}", experience.experience_type, experience.name, experience.model_dump(mode="json"), experience.end_date or experience.start_date))
        for source_key, evidence_type, title, metadata, occurred_at in rows:
            evidence = db.execute(select(GrowthEvidence).where(GrowthEvidence.material_id == material.id, GrowthEvidence.source_key == source_key)).scalar_one_or_none()
            if evidence is None:
                evidence = GrowthEvidence(user_id=user_id, material_id=material.id, source_key=source_key, evidence_type=evidence_type, title=title or evidence_type, source_type="material", verification_status="user_confirmed")
                db.add(evidence)
            evidence.title = title or evidence_type
            evidence.metadata_json = metadata
            evidence.occurred_at = occurred_at
            evidence.verification_status = "user_confirmed"
        material.confirmation_status = "confirmed"
        db.commit()
        return db.execute(select(GrowthEvidence).where(GrowthEvidence.material_id == material.id)).scalars().all()

    def delete(self, db: Session, user_id: str, material_id: str) -> None:
        material = db.execute(select(Material).where(Material.id == material_id, Material.user_id == user_id)).scalar_one_or_none()
        if material is None:
            raise LookupError("材料不存在")
        evidence_ids = select(GrowthEvidence.id).where(GrowthEvidence.material_id == material.id)
        db.execute(delete(AttributeEvidenceLink).where(AttributeEvidenceLink.evidence_id.in_(evidence_ids)))
        db.execute(delete(GrowthEvidence).where(GrowthEvidence.material_id == material.id))
        path = Path(material.storage_path).resolve()
        if self.root in path.parents and path.exists():
            path.unlink()
        db.delete(material); db.commit()
