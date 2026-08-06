import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.groupe import Groupe
from app.models.groupe_employe import GroupeEmploye
from app.models.groupe_planning_recurrent import GroupePlanningRecurrent
from app.models.patient_groupe import PatientGroupe
from app.models.employee_patient_access import EmployeePatientAccess
from app.schemas.groupe import GroupeCreate, GroupeUpdate, GroupePlanningRecurrentCreate


# ─── CRUD Groupe ───────────────────────────────────────────────────────────────

def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[Groupe]:
    return db.query(Groupe).offset(offset).limit(limit).all()


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


# ─── Planning récurrent ────────────────────────────────────────────────────────

def set_planning_recurrent(groupe_id: str, data: GroupePlanningRecurrentCreate, db: Session) -> GroupePlanningRecurrent:
    get_by_id(groupe_id, db)
    planning = GroupePlanningRecurrent(id=str(uuid.uuid4()), groupe_id=groupe_id, **data.model_dump())
    db.add(planning)
    db.commit()
    db.refresh(planning)
    return planning


# ─── Gestion des patients membres ─────────────────────────────────────────────

def _grant_access_idempotent(employee_id: str, patient_id: str, db: Session) -> None:
    """
    Ajoute une entrée dans employee_patient_access si elle n'existe pas encore.
    Idempotent : ne lève pas d'erreur si l'accès est déjà présent.
    """
    existing = (
        db.query(EmployeePatientAccess)
        .filter(
            EmployeePatientAccess.employee_id == employee_id,
            EmployeePatientAccess.patient_id == patient_id,
        )
        .first()
    )
    if not existing:
        db.add(EmployeePatientAccess(employee_id=employee_id, patient_id=patient_id))


def add_patient(groupe_id: str, patient_id: str, db: Session) -> dict:
    """
    Ajoute un patient au groupe.
    Règle métier US-M20 : tous les employés déjà associés au groupe obtiennent
    automatiquement l'accès à ce patient dans employee_patient_access.
    """
    get_by_id(groupe_id, db)
    existing = (
        db.query(PatientGroupe)
        .filter(PatientGroupe.groupe_id == groupe_id, PatientGroupe.patient_id == patient_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Patient déjà dans le groupe")
    db.add(PatientGroupe(patient_id=patient_id, groupe_id=groupe_id))

    # Auto-assignation : chaque employé du groupe accède à ce nouveau patient
    employes = db.query(GroupeEmploye).filter(GroupeEmploye.groupe_id == groupe_id).all()
    for ge in employes:
        _grant_access_idempotent(ge.employe_id, patient_id, db)

    db.commit()
    return {"message": "Patient ajouté au groupe"}


# ─── Gestion des employés responsables (US-M20 / US-M24) ─────────────────────

def get_employes(groupe_id: str, db: Session) -> List[GroupeEmploye]:
    """Retourne la liste des employés associés au groupe."""
    get_by_id(groupe_id, db)
    return db.query(GroupeEmploye).filter(GroupeEmploye.groupe_id == groupe_id).all()


def add_employe(groupe_id: str, employe_id: str, db: Session) -> GroupeEmploye:
    """
    Associe un employé au groupe.
    Règle métier US-M20 : l'employé obtient automatiquement l'accès à tous les
    patients déjà membres du groupe dans employee_patient_access.
    """
    get_by_id(groupe_id, db)
    existing = (
        db.query(GroupeEmploye)
        .filter(GroupeEmploye.groupe_id == groupe_id, GroupeEmploye.employe_id == employe_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet employé est déjà associé au groupe.",
        )

    ge = GroupeEmploye(groupe_id=groupe_id, employe_id=employe_id)
    db.add(ge)

    # Auto-assignation : cet employé accède à tous les patients du groupe
    patients = db.query(PatientGroupe).filter(PatientGroupe.groupe_id == groupe_id).all()
    for pg in patients:
        _grant_access_idempotent(employe_id, pg.patient_id, db)

    db.commit()
    db.refresh(ge)
    return ge


def add_employes(groupe_id: str, employe_ids: List[str], db: Session) -> dict:
    """
    Associe plusieurs employés au groupe en une seule opération.
    Les doublons sont silencieusement ignorés (idempotent).
    """
    get_by_id(groupe_id, db)
    patients = db.query(PatientGroupe).filter(PatientGroupe.groupe_id == groupe_id).all()
    added = 0
    for employe_id in employe_ids:
        existing = (
            db.query(GroupeEmploye)
            .filter(GroupeEmploye.groupe_id == groupe_id, GroupeEmploye.employe_id == employe_id)
            .first()
        )
        if not existing:
            db.add(GroupeEmploye(groupe_id=groupe_id, employe_id=employe_id))
            for pg in patients:
                _grant_access_idempotent(employe_id, pg.patient_id, db)
            added += 1
    db.commit()
    return {"message": f"{added} employé(s) ajouté(s) au groupe."}


def remove_employe(groupe_id: str, employe_id: str, db: Session) -> None:
    """
    Retire un employé du groupe.
    Note : l'accès dans employee_patient_access n'est PAS révoqué automatiquement
    (l'employé peut avoir d'autres raisons d'accéder à ces patients).
    """
    get_by_id(groupe_id, db)
    ge = (
        db.query(GroupeEmploye)
        .filter(GroupeEmploye.groupe_id == groupe_id, GroupeEmploye.employe_id == employe_id)
        .first()
    )
    if not ge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cet employé n'est pas associé à ce groupe.",
        )
    db.delete(ge)
    db.commit()
