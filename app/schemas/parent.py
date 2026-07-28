from typing import Optional
from pydantic import BaseModel
from app.models.parent import EtatCivilEnum


class ParentBase(BaseModel):
    nom: str
    prenom: str
    telephone: str
    etat_civil: EtatCivilEnum
    adresse: Optional[str] = None


class ParentCreate(ParentBase):
    pass


class ParentUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    etat_civil: Optional[EtatCivilEnum] = None
    adresse: Optional[str] = None


class ParentResponse(ParentBase):
    id: str

    model_config = {"from_attributes": True}
