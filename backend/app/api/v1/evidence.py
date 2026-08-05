from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.evidence import EvidenceRead
from app.services.evidence_service import list_evidences, save_upload

router = APIRouter(tags=["evidence"])


@router.get("/evidences", response_model=list[EvidenceRead])
def list_evidence(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[EvidenceRead]:
    return list_evidences(db, current_user.id)


@router.post("/evidences", response_model=EvidenceRead)
def upload_evidence(
    task_id: str | None = Form(default=None),
    evidence_type: str = Form(...),
    description: str | None = Form(default=None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    try:
        return save_upload(db, file, current_user.id, task_id, evidence_type, description)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/evidences/{evidence_id}")
def delete_evidence(evidence_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        from app.services.evidence_service import delete_evidence as delete_service

        delete_service(db, current_user.id, evidence_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"message": "evidence deleted"}
