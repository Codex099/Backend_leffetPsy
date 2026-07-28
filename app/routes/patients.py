from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, AssocierParentRequest
from app.services import patient_service
from app.services.access_control_service import check_patient_access

router = APIRouter(prefix="/api/patients", tags=["Patients"])


@router.get("", response_model=List[PatientResponse])
def list_patients(db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return patient_service.get_all(employee, db)


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return patient_service.create(data, db)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return check_patient_access(patient_id, employee, db)


@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, data: PatientUpdate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return patient_service.update(patient_id, data, db)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    patient_service.delete(patient_id, db)


@router.post("/{patient_id}/parents", status_code=status.HTTP_201_CREATED)
def associer_parent(patient_id: str, data: AssocierParentRequest, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return patient_service.associer_parent(patient_id, data, db)
