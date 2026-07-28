import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.evenement_calendrier import EvenementCalendrier
from app.schemas.calendrier import EvenementCalendrierCreate, EvenementCalendrierUpdate


def get_all(db: Session) -> List[EvenementCalendrier]:
    return db.query(EvenementCalendrier).order_by(EvenementCalendrier.date).all()


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
