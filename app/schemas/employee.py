from typing import Optional, Any
from pydantic import BaseModel, field_validator
from app.models.employee import RoleEmployeEnum


class EmployeeBase(BaseModel):
    nom: str
    prenom: str
    telephone: str
    username: str
    role: RoleEmployeEnum

    @field_validator("nom", "prenom", "username", "telephone", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> Any:
        """Accepte les variantes de casse : 'Psychologue' → 'psychologue'."""
        if isinstance(v, str):
            return v.strip().lower()
        return v


class EmployeeCreate(EmployeeBase):
    # Le client envoie le mot de passe en clair — le backend le hache avant stockage.
    # Les deux clés "password" et "mot_de_passe" sont acceptées (alias).
    password: str

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v: Any) -> Any:
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le mot de passe ne peut pas être vide")
        return v

    model_config = {"populate_by_name": True}


class EmployeeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    username: Optional[str] = None
    role: Optional[RoleEmployeEnum] = None
    password: Optional[str] = None

    @field_validator("nom", "prenom", "username", "telephone", mode="before")
    @classmethod
    def validate_non_empty_str(cls, v: Any, info) -> Any:
        field_name = info.field_name
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError(f"Le champ '{field_name}' ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().lower()
        return v


class EmployeeResponse(EmployeeBase):
    id: str
    # Le champ password_hash n'est JAMAIS exposé dans la réponse API.

    model_config = {"from_attributes": True}


class AssignPatientRequest(BaseModel):
    patient_id: str
