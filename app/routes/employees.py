from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, AssignPatientRequest
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.get_all(db)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.create(data, db)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.get_by_id(employee_id, db)


@router.put("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: str, data: EmployeeUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.update(employee_id, data, db)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    employee_service.delete(employee_id, db)


@router.post("/{employee_id}/patients", status_code=status.HTTP_201_CREATED)
def assign_patient(employee_id: str, data: AssignPatientRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.assign_patient(employee_id, data.patient_id, db)
