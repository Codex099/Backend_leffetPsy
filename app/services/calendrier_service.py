import uuid
from datetime import date as date_type
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.evenement_calendrier import EvenementCalendrier
from app.schemas.calendrier import EvenementCalendrierCreate, EvenementCalendrierUpdate


def get_all(
    db: Session,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    limit: int = 500,
    offset: int = 0,
) -> List[EvenementCalendrier]:
    """
    Événements du calendrier administratif.
    L'écran calendrier charge un mois à la fois via ?date_debut / ?date_fin.
    """
    q = db.query(EvenementCalendrier)
    if date_debut is not None:
        q = q.filter(EvenementCalendrier.date >= date_debut)
    if date_fin is not None:
        q = q.filter(EvenementCalendrier.date <= date_fin)
    return q.order_by(EvenementCalendrier.date).offset(offset).limit(limit).all()


def get_by_id(event_id: str, db: Session) -> EvenementCalendrier:
    e = db.query(EvenementCalendrier).filter(EvenementCalendrier.id == event_id).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Événement introuvable")
    return e


def create(data: EvenementCalendrierCreate, employee_id: str, db: Session) -> EvenementCalendrier:
    event = EvenementCalendrier(id=str(uuid.uuid4()), cree_par=employee_id, **data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def update(event_id: str, data: EvenementCalendrierUpdate, db: Session) -> EvenementCalendrier:
    event = get_by_id(event_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


def delete(event_id: str, db: Session) -> None:
    event = get_by_id(event_id, db)
    db.delete(event)
    db.commit()
