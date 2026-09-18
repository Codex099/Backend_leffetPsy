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


def get_accessible_patient_ids(employee: Employee, db: Session) -> list[str] | None:
    """
    Retourne la liste des patient_ids accessibles pour un employé.
    Retourne None si admin (= tous les patients).
    Inclut :
      1. Les accès explicites dans EmployeePatientAccess
      2. Les patients des séances individuelles où l'employé est assigné (SeanceEmploye)
      3. Les patients des séances de groupe animées par l'employé (SeanceGroupe)
      4. Les patients pour lesquels l'employé a rédigé une note (SeanceGroupeParticipant.redige_par)
    """
    if employee.role == "admin":
        return None  # pas de filtre

    # 1. Accès explicites
    patient_ids = {
        r[0]
        for r in db.query(EmployeePatientAccess.patient_id)
        .filter(EmployeePatientAccess.employee_id == employee.id)
        .all()
    }

    # 2. Séances individuelles assignées
    try:
        from app.models.seance import Seance
        from app.models.seance_employe import SeanceEmploye
        seance_pids = {
            r[0]
            for r in db.query(Seance.patient_id)
            .join(SeanceEmploye, SeanceEmploye.seance_id == Seance.id)
            .filter(SeanceEmploye.employe_id == employee.id, Seance.patient_id.isnot(None))
            .all()
        }
        patient_ids.update(seance_pids)
    except Exception:
        pass

    # 3. Séances de groupe animées
    try:
        from app.models.seance_groupe import SeanceGroupe
        from app.models.seance_groupe_participant import SeanceGroupeParticipant
        groupe_pids = {
            r[0]
            for r in db.query(SeanceGroupeParticipant.patient_id)
            .join(SeanceGroupe, SeanceGroupe.id == SeanceGroupeParticipant.seance_groupe_id)
            .filter(SeanceGroupe.employe_id == employee.id, SeanceGroupeParticipant.patient_id.isnot(None))
            .all()
        }
        patient_ids.update(groupe_pids)
    except Exception:
        pass

    # 4. Notes de groupe rédigées
    try:
        from app.models.seance_groupe_participant import SeanceGroupeParticipant
        redige_pids = {
            r[0]
            for r in db.query(SeanceGroupeParticipant.patient_id)
            .filter(SeanceGroupeParticipant.redige_par == employee.id, SeanceGroupeParticipant.patient_id.isnot(None))
            .all()
        }
        patient_ids.update(redige_pids)
    except Exception:
        pass

    return list(patient_ids)


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

    accessible_ids = get_accessible_patient_ids(employee, db)
    if accessible_ids is not None and patient_id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès à ce patient non autorisé",
        )
    return patient

