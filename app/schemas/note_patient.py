from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel, field_validator


class NotePatientBase(BaseModel):
    contenu: str
    seance_id: Optional[str] = None
    seance_groupe_id: Optional[str] = None
    medias: Optional[Any] = None


class NotePatientCreate(NotePatientBase):
    # Règle de rejet portée par Create, pas par NotePatientBase :
    # NotePatientResponse hérite de NotePatientBase et Pydantic rejoue les
    # validateurs à la sérialisation — une règle ici ferait échouer la liste
    # des notes sur une seule ligne mal formée en base.
    @field_validator("contenu", mode="before")
    @classmethod
    def validate_contenu(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le contenu de la note ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v


class NotePatientResponse(NotePatientBase):
    id: str
    patient_id: str
    employe_id: Optional[str] = None
    date_creation: datetime

    # Auteur imbriqué (enrichment_service) : la note affiche le nom du
    # rédacteur, pas son UUID.
    auteur: Optional[Any] = None

    model_config = {"from_attributes": True}
