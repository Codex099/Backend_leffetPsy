"""
Centralisation du contrôle d'accès aux données médicales.

Règle :
  - admin → accès à tous les patients
  - psychologue / éducatrice → uniquement les patients dans employee_patient_access

Utilisation dans les routes :
    employee = Depends(get_current_employee)
    patient = check_patient_access(patient_id, employee, db)
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.patient import Patient
from app.models.employee_patient_access import EmployeePatientAccess


def check_patient_access(patient_id: str, employee: Employee, db: Session) -> Patient:
    """
    Vérifie que l'employé a le droit d'accéder au patient donné.
    Retourne le patient si l'accès est autorisé, sinon lève une 403 ou 404.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient introuvable")

    if employee.role == "admin":
        return patient

    access = (
        db.query(EmployeePatientAccess)
        .filter(
            EmployeePatientAccess.employee_id == employee.id,
            EmployeePatientAccess.patient_id == patient_id,
        )
        .first()
    )
    if not access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès à ce patient non autorisé",
        )
    return patient


def get_accessible_patient_ids(employee: Employee, db: Session) -> list[str] | None:
    """
    Retourne la liste des patient_ids accessibles pour un employé.
    Retourne None si admin (= tous les patients).
    """
    if employee.role == "admin":
        return None  # pas de filtre
    rows = (
        db.query(EmployeePatientAccess.patient_id)
        .filter(EmployeePatientAccess.employee_id == employee.id)
        .all()
    )
    return [r.patient_id for r in rows]
