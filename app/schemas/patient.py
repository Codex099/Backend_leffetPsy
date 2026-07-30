from typing import Optional
from datetime import date, datetime
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
    est_actif: bool
    date_desactivation: Optional[datetime] = None
    date_reactivation: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AssocierParentRequest(BaseModel):
    parent_id: str
    role: RoleParentEnum


# ─── Statut actif / inactif ───────────────────────────────────────────────────

class ChangerStatutRequest(BaseModel):
    """Payload pour activer ou désactiver un patient."""
    est_actif: bool
    note_degradation: Optional[str] = None  # optionnel lors d'une réactivation

