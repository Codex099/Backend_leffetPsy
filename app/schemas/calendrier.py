from typing import Optional
from datetime import date
from pydantic import BaseModel


class EvenementCalendrierBase(BaseModel):
    titre: str
    description: Optional[str] = None
    date: date
    notifier_avant_jours: Optional[int] = None


class EvenementCalendrierCreate(EvenementCalendrierBase):
    pass


class EvenementCalendrierUpdate(BaseModel):
    titre: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date] = None
    notifier_avant_jours: Optional[int] = None


class EvenementCalendrierResponse(EvenementCalendrierBase):
    id: str
    cree_par: Optional[str] = None

    model_config = {"from_attributes": True}
