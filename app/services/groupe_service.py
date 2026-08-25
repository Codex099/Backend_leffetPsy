import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.groupe import Groupe
from app.models.groupe_employe import GroupeEmploye
from app.models.groupe_planning_recurrent import GroupePlanningRecurrent
from app.models.patient_groupe import PatientGroupe
from app.models.employee_patient_access import EmployeePatientAccess
from app.schemas.groupe import GroupeCreate, GroupeUpdate, GroupePlanningRecurrentCreate
from app.services import enrichment_service


# ─── Enrichissement des réponses ───────────────────────────────────────────────

def _enrich(target, db: Session):
    """
    Attache membres, planning fixe et employés responsables au(x) groupe(s).
    Tout est chargé par lot : 4 requêtes quel que soit le nombre de groupes.
    """
    is_list = isinstance(target, (list, tuple))
    groupes = [g for g in (target if is_list else [target]) if g is not None]
    if not groupes:
        return target
    ids = [g.id for g in groupes]

    liens_patients = db.query(PatientGroupe).filter(PatientGroupe.groupe_id.in_(ids)).all()
    enrichment_service.attach_patient(liens_patients, db)
    patients_par_groupe = enrichment_service.group_by(
        liens_patients, "groupe_id", enrichment_service.linked("patient")
    )

    plannings = db.query(GroupePlanningRecurrent).filter(GroupePlanningRecurrent.groupe_id.in_(ids)).all()
    planning_par_groupe = enrichment_service.group_by(
        plannings, "groupe_id", enrichment_service.groupe_planning_summary
    )

    liens_employes = db.query(GroupeEmploye).filter(GroupeEmploye.groupe_id.in_(ids)).all()
    enrichment_service.attach_employee(liens_employes, db)
    employes_par_groupe = enrichment_service.group_by(
        liens_employes, "groupe_id", enrichment_service.linked("employe")
    )

    for g in groupes:
        g.patients = patients_par_groupe.get(g.id, [])
        g.planning_recurrent = planning_par_groupe.get(g.id, [])
        g.employees = employes_par_groupe.get(g.id, [])
    return target


# ─── CRUD Groupe ───────────────────────────────────────────────────────────────

def get_all(db: Session, search: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Groupe]:
    q = db.query(Groupe)
    if search:
        motif = f"%{search.strip()}%"
        q = q.filter(or_(Groupe.nom.ilike(motif), Groupe.description.ilike(motif)))
    groupes = q.offset(offset).limit(limit).all()
    return _enrich(groupes, db)


def get_by_id(groupe_id: str, db: Session) -> Groupe:
    g = db.query(Groupe).filter(Groupe.id == groupe_id).first()
    if not g:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Groupe introuvable")
    return g


def get_detail(groupe_id: str, db: Session) -> Groupe:
    """Groupe enrichi (membres, planning récurrent, responsables) — écran détail."""
    return _enrich(get_by_id(groupe_id, db), db)


def create(data: GroupeCreate, db: Session) -> Groupe:
    groupe = Groupe(id=str(uuid.uuid4()), **data.model_dump())
    db.add(groupe)
    db.commit()
    db.refresh(groupe)
    return _enrich(groupe, db)


def update(groupe_id: str, data: GroupeUpdate, db: Session) -> Groupe:
    groupe = get_by_id(groupe_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(groupe, field, value)
    db.commit()
    db.refresh(groupe)
    return _enrich(groupe, db)


def delete(groupe_id: str, db: Session) -> None:
    groupe = get_by_id(groupe_id, db)
    db.delete(groupe)
    db.commit()


# ─── Planning récurrent ────────────────────────────────────────────────────────

def get_planning_recurrent(groupe_id: str, db: Session) -> List[GroupePlanningRecurrent]:
    """Créneaux fixes du groupe, triés par jour puis heure de début."""
    get_by_id(groupe_id, db)
    return (
        db.query(GroupePlanningRecurrent)
        .filter(GroupePlanningRecurrent.groupe_id == groupe_id)
        .order_by(GroupePlanningRecurrent.jour_semaine, GroupePlanningRecurrent.heure_debut)
        .all()
    )


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


def get_patients(groupe_id: str, db: Session) -> List[dict]:
    """
    Liste les patients membres du groupe (résumé enrichi : nom, prénom, photo…).
    Alimente l'écran détail du groupe.
    """
    get_by_id(groupe_id, db)
    liens = db.query(PatientGroupe).filter(PatientGroupe.groupe_id == groupe_id).all()
    enrichment_service.attach_patient(liens, db)
    return [lien.patient for lien in liens if lien.patient is not None]


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


def remove_patient(groupe_id: str, patient_id: str, db: Session) -> None:
    """
    Retire un patient du groupe.
    Symétrique de `remove_employe` : l'accès dans employee_patient_access n'est
    PAS révoqué, le patient pouvant être suivi par ailleurs (autre groupe,
    assignation directe).
    """
    get_by_id(groupe_id, db)
    lien = (
        db.query(PatientGroupe)
        .filter(PatientGroupe.groupe_id == groupe_id, PatientGroupe.patient_id == patient_id)
        .first()
    )
    if not lien:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ce patient n'est pas membre de ce groupe.",
        )
    db.delete(lien)
    db.commit()


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
