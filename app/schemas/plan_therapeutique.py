from typing import Optional, List, Any
from datetime import date
from pydantic import BaseModel, field_validator
from app.models.etape_plan_therapeutique import StatutEtapeEnum
from app.models.plan_therapeutique import StatutPlanEnum


# ─── Plans thérapeutiques ─────────────────────────────────────────────────────

class PlanTherapeutiqueBase(BaseModel):
    titre: str
    statut: StatutPlanEnum = StatutPlanEnum.actif
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class PlanTherapeutiqueCreate(PlanTherapeutiqueBase):
    # Règle de rejet portée par Create, pas par la classe Base :
    # PlanTherapeutiqueResponse hérite de ce socle et Pydantic rejoue les
    # validateurs à la sérialisation — une règle ici ferait échouer la liste
    # des plans sur une seule ligne mal formée en base.
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
    etapes: List[EtapeResponse] = []

    model_config = {"from_attributes": True}


# ─── Étapes ───────────────────────────────────────────────────────────────────

class EtapeBase(BaseModel):
    titre: str
    description: Optional[str] = None
    statut: StatutEtapeEnum = StatutEtapeEnum.a_faire
    ordre: int


class EtapeCreate(EtapeBase):
    # Idem : rejet sur Create uniquement, EtapeResponse hérite d'EtapeBase.
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

    model_config = {"from_attributes": True}


class CreerTacheDepuisEtapeRequest(BaseModel):
    assigne_a: str

