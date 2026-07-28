from typing import Optional
from datetime import date
from pydantic import BaseModel
from app.models.patient_parent import RoleParentEnum


class PatientBase(BaseModel):
    nom: str
    prenom: str
    date_naissance: Optional[date] = None
    photo: Optional[str] = None
    nombre_freres_soeurs: Optional[int] = None
    ordre_naissance: Optional[int] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[date] = None
    photo: Optional[str] = None
    nombre_freres_soeurs: Optional[int] = None
    ordre_naissance: Optional[int] = None


class PatientResponse(PatientBase):
    id: str

    model_config = {"from_attributes": True}


class AssocierParentRequest(BaseModel):
    parent_id: str
    role: RoleParentEnum
