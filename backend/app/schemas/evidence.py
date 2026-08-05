from pydantic import BaseModel, Field


class EvidenceCreate(BaseModel):
    task_id: str | None = None
    evidence_type: str = Field(pattern=r"^(input|result|test|application)$")
    description: str | None = None


class EvidenceRead(EvidenceCreate):
    id: str
    file_name: str | None = None
    mime_type: str | None = None

    model_config = {"from_attributes": True}
