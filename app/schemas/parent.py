from typing import Optional, Any
from pydantic import BaseModel, field_validator
from app.models.parent import EtatCivilEnum


class ParentBase(BaseModel):
    nom: str
    prenom: str
    telephone: str
    etat_civil: EtatCivilEnum
    adresse: Optional[str] = None

    @field_validator("nom", "prenom", "telephone", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class ParentCreate(ParentBase):
    pass


class ParentUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    etat_civil: Optional[EtatCivilEnum] = None
    adresse: Optional[str] = None

    @field_validator("nom", "prenom", "telephone", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class ParentResponse(ParentBase):
    id: str

    model_config = {"from_attributes": True}
