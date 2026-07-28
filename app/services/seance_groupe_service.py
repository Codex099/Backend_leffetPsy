import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seance_groupe import SeanceGroupe
from app.models.seance_groupe_participant import SeanceGroupeParticipant
from app.schemas.seance_groupe import SeanceGroupeCreate, SeanceGroupeUpdate, ParticipantUpdate


def get_all(db: Session) -> List[SeanceGroupe]:
    return db.query(SeanceGroupe).all()


def get_by_id(seance_id: str, db: Session) -> SeanceGroupe:
    s = db.query(SeanceGroupe).filter(SeanceGroupe.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Séance de groupe introuvable")
    return s


def create(data: SeanceGroupeCreate, db: Session) -> SeanceGroupe:
    seance = SeanceGroupe(id=str(uuid.uuid4()), **data.model_dump())
    db.add(seance)
    db.commit()
    db.refresh(seance)
    return seance


def update(seance_id: str, data: SeanceGroupeUpdate, db: Session) -> SeanceGroupe:
    seance = get_by_id(seance_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(seance, field, value)
    db.commit()
    db.refresh(seance)
    return seance


def delete(seance_id: str, db: Session) -> None:
    seance = get_by_id(seance_id, db)
    db.delete(seance)
    db.commit()


def update_participant(
    seance_groupe_id: str,
    patient_id: str,
    data: ParticipantUpdate,
    employee_id: str,
    db: Session,
) -> SeanceGroupeParticipant:
    get_by_id(seance_groupe_id, db)
    participant = (
        db.query(SeanceGroupeParticipant)
        .filter(
            SeanceGroupeParticipant.seance_groupe_id == seance_groupe_id,
            SeanceGroupeParticipant.patient_id == patient_id,
        )
        .first()
    )
    if not participant:
        participant = SeanceGroupeParticipant(
            seance_groupe_id=seance_groupe_id,
            patient_id=patient_id,
        )
        db.add(participant)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(participant, field, value)
    participant.redige_par = employee_id
    db.commit()
    db.refresh(participant)
    return participant
