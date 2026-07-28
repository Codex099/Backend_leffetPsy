from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class NotePatientBase(BaseModel):
    contenu: str
    seance_id: Optional[str] = None
    seance_groupe_id: Optional[str] = None
    medias: Optional[Any] = None


class NotePatientCreate(NotePatientBase):
    pass


class NotePatientResponse(NotePatientBase):
    id: str
    patient_id: str
    employe_id: Optional[str] = None
    date_creation: datetime

    model_config = {"from_attributes": True}
