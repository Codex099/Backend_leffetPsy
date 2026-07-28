from typing import Optional, List
from datetime import time
from pydantic import BaseModel
from app.models.groupe import TypePlanningEnum
from app.models.groupe_planning_recurrent import JourSemaineEnum


class GroupeBase(BaseModel):
    nom: str
    type_planning: TypePlanningEnum
    description: Optional[str] = None


class GroupeCreate(GroupeBase):
    pass


class GroupeUpdate(BaseModel):
    nom: Optional[str] = None
    type_planning: Optional[TypePlanningEnum] = None
    description: Optional[str] = None


class GroupeResponse(GroupeBase):
    id: str

    model_config = {"from_attributes": True}


class GroupePlanningRecurrentCreate(BaseModel):
    jour_semaine: JourSemaineEnum
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None


class GroupePlanningRecurrentResponse(GroupePlanningRecurrentCreate):
    id: str
    groupe_id: str

    model_config = {"from_attributes": True}


class AjouterPatientGroupeRequest(BaseModel):
    patient_id: str
