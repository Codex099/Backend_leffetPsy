from typing import Optional
from datetime import datetime
from pydantic import BaseModel
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


class TacheResponse(TacheBase):
    id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}
