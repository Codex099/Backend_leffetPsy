import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.note_patient import NotePatient
from app.schemas.note_patient import NotePatientCreate


def get_by_patient(patient_id: str, db: Session) -> List[NotePatient]:
    return (
        db.query(NotePatient)
        .filter(NotePatient.patient_id == patient_id)
        .order_by(NotePatient.date_creation.desc())
        .all()
    )


def create(patient_id: str, data: NotePatientCreate, employee_id: str, db: Session) -> NotePatient:
    # seance_id et seance_groupe_id mutuellement exclusifs
    if data.seance_id and data.seance_groupe_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="seance_id et seance_groupe_id sont mutuellement exclusifs",
        )
    note = NotePatient(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        employe_id=employee_id,
        **data.model_dump(),
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def delete(note_id: str, employee, db: Session) -> None:
    note = db.query(NotePatient).filter(NotePatient.id == note_id).first()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note introuvable")
    if employee.role != "admin" and note.employe_id != employee.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Suppression non autorisée")
    db.delete(note)
    db.commit()
