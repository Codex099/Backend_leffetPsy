from typing import Optional, List, Any
from datetime import time
from pydantic import BaseModel, field_validator
from app.models.groupe import TypePlanningEnum
from app.models.groupe_planning_recurrent import JourSemaineEnum


class GroupeBase(BaseModel):
    nom: str
    type_planning: TypePlanningEnum
    description: Optional[str] = None

    @field_validator("nom", mode="before")
    @classmethod
    def validate_nom(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le nom du groupe ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class GroupeCreate(GroupeBase):
    pass


class GroupeUpdate(BaseModel):
    nom: Optional[str] = None
    type_planning: Optional[TypePlanningEnum] = None
    description: Optional[str] = None

    @field_validator("nom", mode="before")
    @classmethod
    def validate_nom(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le nom du groupe ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class GroupeResponse(GroupeBase):
    id: str

    model_config = {"from_attributes": True}


class GroupePlanningRecurrentCreate(BaseModel):
    jour_semaine: JourSemaineEnum
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None


class GroupePlanningRecurrentResponse(GroupePlanningRecurrentCreate):
    id: str
    groupe_id: str

    model_config = {"from_attributes": True}


class AjouterPatientGroupeRequest(BaseModel):
    patient_id: str


# ─── Employés responsables d'un groupe (US-M20 / US-M24) ──────────────────────

class AjouterEmployeGroupeRequest(BaseModel):
    """Associe un ou plusieurs employés à un groupe en tant que responsables."""
    employe_id: str


class AjouterEmployesGroupeRequest(BaseModel):
    """Associe plusieurs employés d'un coup à un groupe."""
    employe_ids: List[str]


class GroupeEmployeResponse(BaseModel):
    groupe_id: str
    employe_id: str

    model_config = {"from_attributes": True}
