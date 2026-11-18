from typing import Optional, List, Any
from datetime import date
from pydantic import BaseModel, field_validator
from app.models.etape_plan_therapeutique import StatutEtapeEnum
from app.models.plan_therapeutique import StatutPlanEnum


class EmployeeSimple(BaseModel):
    id: str
    nom: str
    prenom: str
    role: str

    model_config = {"from_attributes": True}


# ─── Sous-Étapes (Séances) ────────────────────────────────────────────────────

class SousEtapeBase(BaseModel):
    titre: str
    description: Optional[str] = None
    statut: StatutEtapeEnum = StatutEtapeEnum.a_faire
    ordre: int = 1
    date_prevue: Optional[date] = None
    assigne_a: Optional[str] = None


class SousEtapeCreate(SousEtapeBase):
    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le titre de la séance ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class SousEtapeUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[StatutEtapeEnum] = None
    ordre: Optional[int] = None
    date_prevue: Optional[date] = None
    assigne_a: Optional[str] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le titre de la séance ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class SousEtapeResponse(SousEtapeBase):
    id: str
    etape_id: str
    cree_par: Optional[str] = None
    assigne_employee: Optional[EmployeeSimple] = None

    model_config = {"from_attributes": True}


# ─── Étapes ───────────────────────────────────────────────────────────────────

class EtapeBase(BaseModel):
    titre: str
    description: Optional[str] = None
    statut: StatutEtapeEnum = StatutEtapeEnum.a_faire
    ordre: int
    assigne_a: Optional[str] = None


class EtapeCreate(EtapeBase):
    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le titre de l'étape ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class EtapeUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[StatutEtapeEnum] = None
    ordre: Optional[int] = None
    assigne_a: Optional[str] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le titre de l'étape ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class EtapeResponse(EtapeBase):
    id: str
    plan_id: str
    cree_par: Optional[str] = None
    assigne_employee: Optional[EmployeeSimple] = None
    sous_etapes: List[SousEtapeResponse] = []

    model_config = {"from_attributes": True}


# ─── Plans thérapeutiques ─────────────────────────────────────────────────────

class PlanTherapeutiqueBase(BaseModel):
    titre: str
    statut: StatutPlanEnum = StatutPlanEnum.actif
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    assigne_a: Optional[str] = None


class PlanTherapeutiqueCreate(PlanTherapeutiqueBase):
    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class PlanTherapeutiqueUpdate(BaseModel):
    titre: Optional[str] = None
    statut: Optional[StatutPlanEnum] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    assigne_a: Optional[str] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class PlanTherapeutiqueResponse(PlanTherapeutiqueBase):
    id: str
    patient_id: str
    cree_par: Optional[str] = None
    assigne_employee: Optional[EmployeeSimple] = None
    etapes: List[EtapeResponse] = []

    model_config = {"from_attributes": True}


# ─── Requêtes d'assignation ───────────────────────────────────────────────────

class AssignerRequest(BaseModel):
    employee_id: Optional[str] = None
    propager: bool = False


class CreerTacheDepuisEtapeRequest(BaseModel):
    assigne_a: str
