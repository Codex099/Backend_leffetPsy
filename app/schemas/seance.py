from typing import Optional, List, Any
from datetime import date, time
from pydantic import BaseModel
from app.models.seance import StatutSeanceEnum, StatutPresenceEnum
from app.models.patient_planning_recurrent import ModeGenerationEnum


class SeanceBase(BaseModel):
    patient_id: str
    date: date
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    statut: StatutSeanceEnum = StatutSeanceEnum.prevue


class SeanceCreate(SeanceBase):
    employe_ids: Optional[List[str]] = []


class SeanceUpdate(BaseModel):
    date: Optional[date] = None
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    statut: Optional[StatutSeanceEnum] = None
    motif_statut: Optional[str] = None
    statut_presence: Optional[StatutPresenceEnum] = None
    description_etat: Optional[str] = None
    reponses_questionnaire: Optional[Any] = None
    medias: Optional[Any] = None
    employe_ids: Optional[List[str]] = None


class SeanceResponse(SeanceBase):
    id: str
    motif_statut: Optional[str] = None
    statut_presence: Optional[StatutPresenceEnum] = None
    description_etat: Optional[str] = None
    reponses_questionnaire: Optional[Any] = None
    medias: Optional[Any] = None

    model_config = {"from_attributes": True}


class PatientPlanningRecurrentCreate(BaseModel):
    jours_semaine: List[str]
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    date_debut: date
    date_fin: Optional[date] = None
    employe_id: Optional[str] = None
    mode_generation: ModeGenerationEnum
    horizon_jours: Optional[int] = None


class PatientPlanningRecurrentResponse(PatientPlanningRecurrentCreate):
    id: str
    patient_id: str

    model_config = {"from_attributes": True}


class GenererCreneauxRequest(BaseModel):
    date_debut: date
    date_fin: date
