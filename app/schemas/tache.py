from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, field_validator
from app.models.tache import StatutTacheEnum, PrioriteTacheEnum


class TacheBase(BaseModel):
    titre: str
    description: Optional[str] = None
    assigne_a: Optional[str] = None
    patient_id: Optional[str] = None
    etape_plan_id: Optional[str] = None
    statut: StatutTacheEnum = StatutTacheEnum.a_faire
    priorite: PrioriteTacheEnum = PrioriteTacheEnum.normale
    date_echeance: Optional[datetime] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le titre de la tâche ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class TacheCreate(TacheBase):
    pass


class TacheUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    assigne_a: Optional[str] = None
    patient_id: Optional[str] = None
    statut: Optional[StatutTacheEnum] = None
    priorite: Optional[PrioriteTacheEnum] = None
    date_echeance: Optional[datetime] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le titre de la tâche ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class TacheResponse(TacheBase):
    id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}
