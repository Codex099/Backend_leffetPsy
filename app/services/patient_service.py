import uuid
from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient, SexeEnum
from app.models.patient_parent import PatientParent
from app.models.dossier_medical import DossierMedical
from app.schemas.patient import PatientCreate, PatientUpdate, AssocierParentRequest
from app.services.access_control_service import get_accessible_patient_ids


def _get_max_birth_date(age_min: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - age_min)
    except ValueError:
        return today.replace(year=today.year - age_min, day=28)


def _get_min_birth_date(age_max: int) -> date:
    today = date.today()
    try:
        return today.replace(year=today.year - age_max - 1)
    except ValueError:
        return today.replace(year=today.year - age_max - 1, day=28)


def get_all(
    employee,
    db: Session,
    actif: Optional[bool] = None,
    sexe: Optional[SexeEnum] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Patient]:
    patient_ids = get_accessible_patient_ids(employee, db)
    q = db.query(Patient)
    if patient_ids is not None:
        q = q.filter(Patient.id.in_(patient_ids))
    if actif is not None:
        q = q.filter(Patient.est_actif == actif)
    if sexe is not None:
        q = q.filter(Patient.sexe == sexe)
    if age_min is not None:
        q = q.filter(Patient.date_naissance.isnot(None), Patient.date_naissance <= _get_max_birth_date(age_min))
    if age_max is not None:
        q = q.filter(Patient.date_naissance.isnot(None), Patient.date_naissance > _get_min_birth_date(age_max))
    return q.offset(offset).limit(limit).all()



def get_by_id(patient_id: str, db: Session) -> Patient:
    p = db.query(Patient).filter(Patient.id == patient_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient introuvable")
    return p


def create(data: PatientCreate, db: Session) -> Patient:
    patient = Patient(id=str(uuid.uuid4()), **data.model_dump())
    db.add(patient)
    db.flush()

    # Créer automatiquement un dossier médical vide
    dossier = DossierMedical(id=str(uuid.uuid4()), patient_id=patient.id)
    db.add(dossier)
    db.commit()
    db.refresh(patient)
    return patient


def update(patient_id: str, data: PatientUpdate, db: Session) -> Patient:
    patient = get_by_id(patient_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


def delete(patient_id: str, db: Session) -> None:
    patient = get_by_id(patient_id, db)
    db.delete(patient)
    db.commit()


def associer_parent(patient_id: str, data: AssocierParentRequest, db: Session) -> dict:
    # Vérifier que le patient existe
    get_by_id(patient_id, db)

    # Éviter les doublons
    existing = (
        db.query(PatientParent)
        .filter(PatientParent.patient_id == patient_id, PatientParent.parent_id == data.parent_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Parent déjà associé")

    lien = PatientParent(patient_id=patient_id, parent_id=data.parent_id, role=data.role)
    db.add(lien)
    db.commit()
    return {"message": "Parent associé avec succès"}
