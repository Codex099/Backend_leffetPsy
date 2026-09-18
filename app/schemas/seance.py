from typing import Optional, List, Any
from datetime import date, time
from pydantic import BaseModel, model_validator
from app.models.seance import StatutSeanceEnum, StatutPresenceEnum
from app.models.patient_planning_recurrent import ModeGenerationEnum


class SeanceBase(BaseModel):
    patient_id: str
    date: date
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    statut: StatutSeanceEnum = StatutSeanceEnum.prevue

    @model_validator(mode="after")
    def validate_heures(self):
        if self.heure_debut is not None and self.heure_fin is not None:
            if self.heure_fin <= self.heure_debut:
                raise ValueError("L'heure de fin doit être strictement postérieure à l'heure de début.")
        return self


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
    employe_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_heures(self):
        if self.heure_debut is not None and self.heure_fin is not None:
            if self.heure_fin <= self.heure_debut:
                raise ValueError("L'heure de fin doit être strictement postérieure à l'heure de début.")
        return self


class SeanceResponse(SeanceBase):
    id: str
    motif_statut: Optional[str] = None
    statut_presence: Optional[StatutPresenceEnum] = None
    description_etat: Optional[str] = None
    reponses_questionnaire: Optional[Any] = None
    medias: Optional[Any] = None

    # Patient imbriqué (enrichment_service) : l'agenda et le dashboard affichent
    # le nom du patient, pas son UUID.
    patient: Optional[Any] = None
    employe_ids: Optional[List[str]] = []

    model_config = {"from_attributes": True}


class PatientPlanningRecurrentCreate(BaseModel):
    jours_semaine: List[str]
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    date_debut: date
    date_fin: Optional[date] = None
    employe_id: Optional[str] = None
    mode_generation: ModeGenerationEnum = ModeGenerationEnum.manuel
    horizon_jours: Optional[int] = 28

    @model_validator(mode="after")
    def validate_heures(self):
        if self.heure_debut is not None and self.heure_fin is not None:
            if self.heure_fin <= self.heure_debut:
                raise ValueError("L'heure de fin doit être strictement postérieure à l'heure de début.")
        return self


class PatientPlanningRecurrentResponse(PatientPlanningRecurrentCreate):
    id: str
    patient_id: str

    model_config = {"from_attributes": True}


class GenererCreneauxRequest(BaseModel):
    date_debut: date
    date_fin: date
