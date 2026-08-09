from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.growth import AttributeEvidenceLink, EvidencePresentation, GrowthAttribute, GrowthEvidence, Material


class InventoryService:
    def list(self, db: Session, user_id: str, evidence_type: str | None = None, attribute_key: str | None = None, relevant_only: bool = False, relevant_attributes: set[str] | None = None) -> list[dict]:
        rows = db.execute(select(GrowthEvidence).where(GrowthEvidence.user_id == user_id).order_by(GrowthEvidence.created_at.desc())).scalars().all()
        result = []
        for evidence in rows:
            if evidence_type and evidence.evidence_type != evidence_type: continue
            attributes = db.execute(select(GrowthAttribute.attribute_key).join(AttributeEvidenceLink, AttributeEvidenceLink.attribute_id == GrowthAttribute.id).where(AttributeEvidenceLink.evidence_id == evidence.id)).scalars().all()
            if attribute_key and attribute_key not in attributes: continue
            presentation = db.get(EvidencePresentation, evidence.id)
            related = bool(set(attributes) & relevant_attributes) if relevant_attributes is not None else False
            if relevant_only and (not related or (presentation and presentation.hidden_from_current_goal)): continue
            material = db.get(Material, evidence.material_id) if evidence.material_id else None
            meta = evidence.metadata_json or {}
            result.append({"id": evidence.id, "name": evidence.title, "type": evidence.evidence_type, "acquired_at": evidence.created_at, "source": evidence.source_type, "attribute_keys": attributes, "verification_status": evidence.verification_status, "goal_relevance": "related" if related else "not_related" if relevant_attributes is not None else "goal_not_selected", "task_id": meta.get("task_id"), "material_id": evidence.material_id, "original_material": material.original_filename if material else None, "expired": bool(evidence.valid_until and evidence.valid_until < date.today()), "description": evidence.description, "user_note": presentation.user_note if presentation else None, "hidden": presentation.hidden_from_current_goal if presentation else False})
        return result

    def update_presentation(self, db: Session, user_id: str, evidence_id: str, note: str | None, hidden: bool) -> None:
        evidence = db.execute(select(GrowthEvidence).where(GrowthEvidence.id == evidence_id, GrowthEvidence.user_id == user_id)).scalar_one_or_none()
        if evidence is None: raise LookupError("背包物品不存在")
        row = db.get(EvidencePresentation, evidence_id)
        if row is None: row = EvidencePresentation(evidence_id=evidence_id, user_id=user_id); db.add(row)
        row.user_note, row.hidden_from_current_goal = note, hidden; db.commit()
