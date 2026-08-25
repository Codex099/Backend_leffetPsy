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

    # Objets imbriqués (enrichment_service) : nom du groupe, animateur et
    # liste des participants avec leur patient.
    groupe: Optional[Any] = None
    employe: Optional[Any] = None
    participants: Optional[Any] = None

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

    # Patient imbriqué : les cartes de suivi du compte-rendu de groupe
    # affichent le nom du participant.
    patient: Optional[Any] = None

    model_config = {"from_attributes": True}
