from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, field_validator


class NotePatientBase(BaseModel):
    contenu: str
    seance_id: Optional[str] = None
    seance_groupe_id: Optional[str] = None
    medias: Optional[Any] = None

    @field_validator("contenu", mode="before")
    @classmethod
    def validate_contenu(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le contenu de la note ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class NotePatientCreate(NotePatientBase):
    pass


class NotePatientResponse(NotePatientBase):
    id: str
    patient_id: str
    employe_id: Optional[str] = None
    date_creation: datetime

    model_config = {"from_attributes": True}
