import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.groupe import Groupe
from app.models.groupe_planning_recurrent import GroupePlanningRecurrent
from app.models.patient_groupe import PatientGroupe
from app.schemas.groupe import GroupeCreate, GroupeUpdate, GroupePlanningRecurrentCreate


def get_all(db: Session) -> List[Groupe]:
    return db.query(Groupe).all()


def get_by_id(groupe_id: str, db: Session) -> Groupe:
    g = db.query(Groupe).filter(Groupe.id == groupe_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return g


def create(data: GroupeCreate, db: Session) -> Groupe:
    groupe = Groupe(id=str(uuid.uuid4()), **data.model_dump())
    db.add(groupe)
    db.commit()
    db.refresh(groupe)
    return groupe


def update(groupe_id: str, data: GroupeUpdate, db: Session) -> Groupe:
    groupe = get_by_id(groupe_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(groupe, field, value)
    db.commit()
    db.refresh(groupe)
    return groupe


def delete(groupe_id: str, db: Session) -> None:
    groupe = get_by_id(groupe_id, db)
    db.delete(groupe)
    db.commit()


def set_planning_recurrent(groupe_id: str, data: GroupePlanningRecurrentCreate, db: Session) -> GroupePlanningRecurrent:
    get_by_id(groupe_id, db)
    planning = GroupePlanningRecurrent(id=str(uuid.uuid4()), groupe_id=groupe_id, **data.model_dump())
    db.add(planning)
    db.commit()
    db.refresh(planning)
    return planning


def add_patient(groupe_id: str, patient_id: str, db: Session) -> dict:
    get_by_id(groupe_id, db)
    existing = (
        db.query(PatientGroupe)
        .filter(PatientGroupe.groupe_id == groupe_id, PatientGroupe.patient_id == patient_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient déjà dans le groupe")
    db.add(PatientGroupe(patient_id=patient_id, groupe_id=groupe_id))
    db.commit()
    return {"message": "Patient ajouté au groupe"}
