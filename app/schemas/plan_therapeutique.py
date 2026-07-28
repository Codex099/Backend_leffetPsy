from typing import Optional, List
from pydantic import BaseModel
from app.models.etape_plan_therapeutique import StatutEtapeEnum


class PlanTherapeutiqueResponse(BaseModel):
    id: str
    patient_id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}


class EtapeBase(BaseModel):
    titre: str
    description: Optional[str] = None
    statut: StatutEtapeEnum = StatutEtapeEnum.a_faire
    ordre: int


class EtapeCreate(EtapeBase):
    pass


class EtapeUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[StatutEtapeEnum] = None
    ordre: Optional[int] = None


class EtapeResponse(EtapeBase):
    id: str
    plan_id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}


class CreerTacheDepuisEtapeRequest(BaseModel):
    assigne_a: str
