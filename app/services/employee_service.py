import re
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.employee_patient_access import EmployeePatientAccess
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, AssignPatientRequest
from app.core.security import hash_password


def _enrich_employee(target, db: Session):
    """Attache la liste des IDs de patients assignés à l'employé."""
    if not target:
        return target
    items = target if isinstance(target, list) else [target]
    emp_ids = [e.id for e in items if hasattr(e, "id") and e.id]
    if emp_ids:
        rows = (
            db.query(EmployeePatientAccess.employee_id, EmployeePatientAccess.patient_id)
            .filter(EmployeePatientAccess.employee_id.in_(emp_ids))
            .all()
        )
        mapping = {}
        for e_id, p_id in rows:
            mapping.setdefault(e_id, []).append(p_id)
        for e in items:
            setattr(e, "patients_assignes_ids", mapping.get(e.id, []))
    return target


def get_all(db: Session, search: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Employee]:
    q = db.query(Employee)
    if search:
        motif = f"%{search.strip()}%"
        q = q.filter(or_(
            Employee.nom.ilike(motif),
            Employee.prenom.ilike(motif),
            Employee.telephone.ilike(motif),
            Employee.username.ilike(motif),
        ))
    employees = q.order_by(Employee.nom, Employee.prenom).offset(offset).limit(limit).all()
    return _enrich_employee(employees, db)


def get_by_id(employee_id: str, db: Session) -> Employee:
    e = db.query(Employee).filter(Employee.id == employee_id).first()
    if not e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé introuvable")
    return _enrich_employee(e, db)


def create(data: EmployeeCreate, db: Session) -> Employee:
    username = data.username.strip()
    telephone = re.sub(r'[\s\.\-]', '', data.telephone.strip()) if data.telephone else ""

    # Vérifier unicité username et téléphone
    if db.query(Employee).filter(Employee.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce nom d'utilisateur est déjà utilisé.")
    if telephone and db.query(Employee).filter(Employee.telephone == telephone).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce numéro de téléphone est déjà utilisé.")

    employee = Employee(
        id=str(uuid.uuid4()),
        nom=data.nom.strip(),
        prenom=data.prenom.strip(),
        telephone=telephone,
        username=username,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return _enrich_employee(employee, db)


def update(employee_id: str, data: EmployeeUpdate, db: Session) -> Employee:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé introuvable")

    update_data = data.model_dump(exclude_unset=True)

    # Vérifier unicité du username si modifié
    if "username" in update_data and update_data["username"]:
        username = update_data["username"].strip()
        existing = db.query(Employee).filter(Employee.username == username, Employee.id != employee_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce nom d'utilisateur est déjà utilisé par un autre employé.")
        update_data["username"] = username

    # Nettoyer et vérifier unicité du téléphone si modifié
    if "telephone" in update_data and update_data["telephone"]:
        telephone = re.sub(r'[\s\.\-]', '', update_data["telephone"].strip())
        existing = db.query(Employee).filter(Employee.telephone == telephone, Employee.id != employee_id).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce numéro de téléphone est déjà utilisé par un autre employé.")
        update_data["telephone"] = telephone

    if "password" in update_data:
        pwd = update_data.pop("password")
        if pwd and pwd.strip():
            update_data["password_hash"] = hash_password(pwd.strip())

    for field, value in update_data.items():
        setattr(employee, field, value)
    db.commit()
    db.refresh(employee)
    return _enrich_employee(employee, db)


def delete(employee_id: str, db: Session) -> None:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employé introuvable")
    # Supprimer les accès patients associés
    db.query(EmployeePatientAccess).filter(EmployeePatientAccess.employee_id == employee_id).delete()
    db.delete(employee)
    db.commit()


def assign_patient(employee_id: str, data: AssignPatientRequest, db: Session) -> dict:
    get_by_id(employee_id, db)

    # Récupérer la liste des patients à assigner
    target_ids = set()
    if data.patient_ids is not None:
        target_ids.update([p for p in data.patient_ids if p])
    elif data.patient_id:
        target_ids.add(data.patient_id)

    # Synchroniser les accès : remplacer par les IDs cibles
    db.query(EmployeePatientAccess).filter(EmployeePatientAccess.employee_id == employee_id).delete()
    for pid in target_ids:
        db.add(EmployeePatientAccess(employee_id=employee_id, patient_id=pid))
    db.commit()

    return {"message": "Patients assignés avec succès", "count": len(target_ids)}


def get_visibility_details(employee_id: str, db: Session) -> dict:
    employee = get_by_id(employee_id, db)
    from app.models.patient import Patient
    all_patients = db.query(Patient).filter(Patient.est_actif == True).order_by(Patient.nom, Patient.prenom).all()
    assigned_ids = set(
        r[0] for r in db.query(EmployeePatientAccess.patient_id).filter(
            EmployeePatientAccess.employee_id == employee_id
        ).all()
    )

    visible = []
    invisible = []
    for p in all_patients:
        item = {
            "id": p.id,
            "nom": p.nom,
            "prenom": p.prenom,
            "sexe": p.sexe.value if hasattr(p.sexe, "value") and p.sexe else p.sexe,
            "date_naissance": str(p.date_naissance) if p.date_naissance else None,
            "photo": p.photo,
            "est_actif": p.est_actif,
        }
        if p.id in assigned_ids:
            visible.append(item)
        else:
            invisible.append(item)

    return {
        "employee": {
            "id": employee.id,
            "nom": employee.nom,
            "prenom": employee.prenom,
            "username": employee.username,
            "role": employee.role.value if hasattr(employee.role, "value") else employee.role,
            "telephone": employee.telephone,
        },
        "visible_patients": visible,
        "invisible_patients": invisible,
        "total_patients": len(all_patients),
        "visible_count": len(visible),
        "invisible_count": len(invisible),
    }


def apply_global_visibility(data, db: Session) -> dict:
    from app.models.patient import Patient
    q = db.query(Employee).filter(Employee.role != "admin")
    if getattr(data, "employee_ids", None):
        q = q.filter(Employee.id.in_(data.employee_ids))
    target_employees = q.all()

    all_patient_ids = [p.id for p in db.query(Patient.id).filter(Patient.est_actif == True).all()]
    affected = 0

    if data.action == "grant_all":
        for emp in target_employees:
            db.query(EmployeePatientAccess).filter(EmployeePatientAccess.employee_id == emp.id).delete()
            for pid in all_patient_ids:
                db.add(EmployeePatientAccess(employee_id=emp.id, patient_id=pid))
            affected += 1
    elif data.action == "revoke_all":
        for emp in target_employees:
            db.query(EmployeePatientAccess).filter(EmployeePatientAccess.employee_id == emp.id).delete()
            affected += 1
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action non reconnue. Utilisez 'grant_all' ou 'revoke_all'."
        )

    db.commit()
    return {
        "message": "Visibilité globale mise à jour avec succès.",
        "action": data.action,
        "affected_employees": affected,
    }
