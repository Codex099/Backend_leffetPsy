from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.note_patient import NotePatientCreate, NotePatientResponse
from app.services import note_patient_service
from app.services.access_control_service import check_patient_access

router = APIRouter(tags=["Notes Patients"])


@router.get("/api/patients/{patient_id}/notes", response_model=List[NotePatientResponse])
def list_notes(
    patient_id: str,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    check_patient_access(patient_id, employee, db)
    return note_patient_service.get_by_patient(patient_id, db)


@router.post("/api/patients/{patient_id}/notes", response_model=NotePatientResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    patient_id: str,
    data: NotePatientCreate,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    check_patient_access(patient_id, employee, db)
    return note_patient_service.create(patient_id, data, employee.id, db)


@router.delete("/api/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: str,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    note_patient_service.delete(note_id, employee, db)
