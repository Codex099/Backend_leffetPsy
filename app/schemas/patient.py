from typing import Optional, Any
from datetime import date, datetime
from pydantic import BaseModel, field_validator
from app.models.patient_parent import RoleParentEnum
from app.models.patient import SexeEnum


class PatientBase(BaseModel):
    nom: str
    prenom: str
    sexe: Optional[SexeEnum] = None
    date_naissance: Optional[date] = None
    photo: Optional[str] = None
    nombre_freres_soeurs: Optional[int] = None
    ordre_naissance: Optional[int] = None

    @field_validator("nom", "prenom", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    sexe: Optional[SexeEnum] = None
    date_naissance: Optional[date] = None
    photo: Optional[str] = None
    nombre_freres_soeurs: Optional[int] = None
    ordre_naissance: Optional[int] = None

    @field_validator("nom", "prenom", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


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

