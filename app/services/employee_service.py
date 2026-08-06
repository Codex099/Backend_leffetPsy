import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.employee_patient_access import EmployeePatientAccess
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.core.security import hash_password


def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[Employee]:
    return db.query(Employee).offset(offset).limit(limit).all()


def get_by_id(employee_id: str, db: Session) -> Employee:
    e = db.query(Employee).filter(Employee.id == employee_id).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé introuvable")
    return e


def create(data: EmployeeCreate, db: Session) -> Employee:
    # Vérifier unicité username et téléphone
    if db.query(Employee).filter(Employee.username == data.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username déjà utilisé")
    if db.query(Employee).filter(Employee.telephone == data.telephone).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Téléphone déjà utilisé")

    employee = Employee(
        id=str(uuid.uuid4()),
        nom=data.nom,
        prenom=data.prenom,
        telephone=data.telephone,
        username=data.username,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update(employee_id: str, data: EmployeeUpdate, db: Session) -> Employee:
    employee = get_by_id(employee_id, db)
    update_data = data.model_dump(exclude_unset=True)

    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return employee


def delete(employee_id: str, db: Session) -> None:
    employee = get_by_id(employee_id, db)
    db.delete(employee)
    db.commit()


def assign_patient(employee_id: str, patient_id: str, db: Session) -> dict:
    get_by_id(employee_id, db)
    existing = (
        db.query(EmployeePatientAccess)
        .filter(
            EmployeePatientAccess.employee_id == employee_id,
            EmployeePatientAccess.patient_id == patient_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Accès déjà existant")
    db.add(EmployeePatientAccess(employee_id=employee_id, patient_id=patient_id))
    db.commit()
    return {"message": "Patient assigné avec succès"}
