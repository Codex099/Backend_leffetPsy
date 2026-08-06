import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seance import Seance
from app.models.seance_employe import SeanceEmploye
from app.models.patient_planning_recurrent import PatientPlanningRecurrent
from app.schemas.seance import SeanceCreate, SeanceUpdate, PatientPlanningRecurrentCreate
from app.services.access_control_service import get_accessible_patient_ids


def get_all(employee, db: Session, limit: int = 100, offset: int = 0) -> List[Seance]:
    patient_ids = get_accessible_patient_ids(employee, db)
    q = db.query(Seance)
    if patient_ids is not None:
        q = q.filter(Seance.patient_id.in_(patient_ids))
    return q.order_by(Seance.date.desc()).offset(offset).limit(limit).all()


def get_by_id(seance_id: str, db: Session) -> Seance:
    s = db.query(Seance).filter(Seance.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Séance introuvable")
    return s


def create(data: SeanceCreate, db: Session) -> Seance:
    seance_data = data.model_dump(exclude={"employe_ids"})
    seance = Seance(id=str(uuid.uuid4()), **seance_data)
    db.add(seance)
    db.flush()

    for emp_id in (data.employe_ids or []):
        db.add(SeanceEmploye(seance_id=seance.id, employe_id=emp_id))

    db.commit()
    db.refresh(seance)
    return seance


def update(seance_id: str, data: SeanceUpdate, db: Session) -> Seance:
    seance = get_by_id(seance_id, db)
    update_data = data.model_dump(exclude_unset=True, exclude={"employe_ids"})
    for field, value in update_data.items():
        setattr(seance, field, value)

    if data.employe_ids is not None:
        db.query(SeanceEmploye).filter(SeanceEmploye.seance_id == seance_id).delete()
        for emp_id in data.employe_ids:
            db.add(SeanceEmploye(seance_id=seance_id, employe_id=emp_id))

    db.commit()
    db.refresh(seance)
    return seance


def delete(seance_id: str, db: Session) -> None:
    seance = get_by_id(seance_id, db)
    db.delete(seance)
    db.commit()


# ── Planning récurrent ─────────────────────────────────────────────────────────

def get_planning_recurrent(patient_id: str, db: Session) -> Optional[PatientPlanningRecurrent]:
    return db.query(PatientPlanningRecurrent).filter(
        PatientPlanningRecurrent.patient_id == patient_id
    ).first()


def set_planning_recurrent(patient_id: str, data: PatientPlanningRecurrentCreate, db: Session) -> PatientPlanningRecurrent:
    existing = get_planning_recurrent(patient_id, db)
    if existing:
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    planning = PatientPlanningRecurrent(id=str(uuid.uuid4()), patient_id=patient_id, **data.model_dump())
    db.add(planning)
    db.commit()
    db.refresh(planning)
    return planning
