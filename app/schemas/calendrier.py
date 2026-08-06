from typing import Optional, Any
from datetime import date
from pydantic import BaseModel, field_validator


def _parse_date(v: Any) -> Any:
    """
    Accepte :
    - Un objet `date` Python natif
    - Une chaîne ISO date  : "YYYY-MM-DD"
    - Une chaîne ISO datetime : "YYYY-MM-DDTHH:MM:SS..." (Flutter/Dart envoie parfois ce format)
    Lève une ValueError explicite si le format est invalide.
    """
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        # Tronquer la partie heure si présente (ex: "2026-08-02T14:30:00Z")
        date_part = v.split("T")[0].split(" ")[0].strip()
        try:
            return date.fromisoformat(date_part)
        except ValueError:
            raise ValueError(
                f"Format de date invalide '{v}' — format attendu : YYYY-MM-DD (ou YYYY-MM-DDTHH:MM:SS)"
            )
    raise ValueError(f"Type non supporté pour 'date' : {type(v).__name__}")


class EvenementCalendrierBase(BaseModel):
    titre: str
    description: Optional[str] = None
    date: date
    notifier_avant_jours: Optional[int] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: Any) -> Any:
        return _parse_date(v)


class EvenementCalendrierCreate(EvenementCalendrierBase):
    pass


class EvenementCalendrierUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    notifier_avant_jours: Optional[int] = None

    @field_validator("titre", mode="before")
    @classmethod
    def validate_titre(cls, v: Any) -> Any:
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Le titre ne peut pas être vide")
        return v.strip() if isinstance(v, str) else v

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: Any) -> Any:
        if v is None:
            return v
        return _parse_date(v)


class EvenementCalendrierResponse(EvenementCalendrierBase):
    id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}

