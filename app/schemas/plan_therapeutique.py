from typing import Optional, List
from datetime import date
from pydantic import BaseModel
from app.models.etape_plan_therapeutique import StatutEtapeEnum
from app.models.plan_therapeutique import StatutPlanEnum


# ─── Plans thérapeutiques ─────────────────────────────────────────────────────

class PlanTherapeutiqueBase(BaseModel):
    titre: str
    statut: StatutPlanEnum = StatutPlanEnum.actif
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class PlanTherapeutiqueCreate(PlanTherapeutiqueBase):
    pass


class PlanTherapeutiqueUpdate(BaseModel):
    titre: Optional[str] = None
    statut: Optional[StatutPlanEnum] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class PlanTherapeutiqueResponse(PlanTherapeutiqueBase):
    id: str
    patient_id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Étapes ───────────────────────────────────────────────────────────────────

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

