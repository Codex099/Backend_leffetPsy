from typing import Optional, Any
from pydantic import BaseModel, field_validator
from app.models.parent import EtatCivilEnum


class ParentBase(BaseModel):
    nom: str
    prenom: str
    telephone: str
    etat_civil: Optional[EtatCivilEnum] = EtatCivilEnum.autre
    adresse: Optional[str] = None

    @field_validator("etat_civil", mode="before")
    @classmethod
    def normalize_etat_civil(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            return EtatCivilEnum.autre
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if "mari" in v_clean:
                return EtatCivilEnum.marie
            if "divorc" in v_clean or "spar" in v_clean or "sépar" in v_clean:
                return EtatCivilEnum.divorce
            if v_clean in ["celibataire", "célibataire", "veuf", "veuve", "autre", "non specifie", "non spécifié"]:
                return EtatCivilEnum.autre
            try:
                return EtatCivilEnum(v_clean)
            except ValueError:
                return EtatCivilEnum.autre
        return v


class ParentCreate(ParentBase):
    @field_validator("nom", "prenom", "telephone", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        if field_name == "telephone" and isinstance(v, str):
            cleaned = "".join(v.split())
            return cleaned
        return v.strip() if isinstance(v, str) else v


class ParentUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    etat_civil: Optional[EtatCivilEnum] = None
    adresse: Optional[str] = None

    @field_validator("etat_civil", mode="before")
    @classmethod
    def normalize_etat_civil(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            return EtatCivilEnum.autre
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if "mari" in v_clean:
                return EtatCivilEnum.marie
            if "divorc" in v_clean or "spar" in v_clean or "sépar" in v_clean:
                return EtatCivilEnum.divorce
            if v_clean in ["celibataire", "célibataire", "veuf", "veuve", "autre", "non specifie", "non spécifié"]:
                return EtatCivilEnum.autre
            try:
                return EtatCivilEnum(v_clean)
            except ValueError:
                return EtatCivilEnum.autre
        return v

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
