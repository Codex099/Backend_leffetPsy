from typing import Optional, Any
from datetime import date, time
from pydantic import BaseModel
from app.models.seance_groupe import StatutSeanceGroupeEnum
from app.models.seance_groupe_participant import StatutPresenceGroupeEnum


class SeanceGroupeBase(BaseModel):
    groupe_id: str
    employe_id: Optional[str] = None
    date: date
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    statut: StatutSeanceGroupeEnum = StatutSeanceGroupeEnum.prevue


class SeanceGroupeCreate(SeanceGroupeBase):
    pass


class SeanceGroupeUpdate(BaseModel):
    employe_id: Optional[str] = None
    date: Optional[date] = None
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None
    statut: Optional[StatutSeanceGroupeEnum] = None


class SeanceGroupeResponse(SeanceGroupeBase):
    id: str

    model_config = {"from_attributes": True}


class ParticipantUpdate(BaseModel):
    statut_presence: Optional[StatutPresenceGroupeEnum] = None
    description_etat: Optional[str] = None
    reponses_questionnaire: Optional[Any] = None
    medias: Optional[Any] = None


class ParticipantResponse(ParticipantUpdate):
    seance_groupe_id: str
    patient_id: str
    redige_par: Optional[str] = None

    model_config = {"from_attributes": True}
