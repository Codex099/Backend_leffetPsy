import uuid
from datetime import date as date_type
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seance import Seance, StatutSeanceEnum
from app.models.seance_employe import SeanceEmploye
from app.models.patient_planning_recurrent import PatientPlanningRecurrent
from app.schemas.seance import SeanceCreate, SeanceUpdate, PatientPlanningRecurrentCreate
from app.services import enrichment_service
from app.services.access_control_service import get_accessible_patient_ids


def _enrich(target, db: Session):
    """Attache le patient et les employe_ids : l'agenda et le dashboard affichent le nom et les praticiens."""
    if not target:
        return target
    items = target if isinstance(target, list) else [target]
    seance_ids = [s.id for s in items if hasattr(s, "id") and s.id]
    if seance_ids:
        rows = db.query(SeanceEmploye.seance_id, SeanceEmploye.employe_id).filter(
            SeanceEmploye.seance_id.in_(seance_ids)
        ).all()
        mapping = {}
        for s_id, e_id in rows:
            mapping.setdefault(s_id, []).append(e_id)
        for s in items:
            setattr(s, "employe_ids", mapping.get(s.id, []))
    return enrichment_service.attach_patient(target, db)


def get_all(
    employee,
    db: Session,
    patient_id: Optional[str] = None,
    date: Optional[date_type] = None,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    statut: Optional[StatutSeanceEnum] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Seance]:
    patient_ids = get_accessible_patient_ids(employee, db)
    q = db.query(Seance)
    # Le périmètre d'accès s'applique toujours : les filtres s'y ajoutent.
    if patient_ids is not None:
        q = q.filter(Seance.patient_id.in_(patient_ids))
    if patient_id is not None:
        q = q.filter(Seance.patient_id == patient_id)
    if date is not None:
        q = q.filter(Seance.date == date)
    if date_debut is not None:
        q = q.filter(Seance.date >= date_debut)
    if date_fin is not None:
        q = q.filter(Seance.date <= date_fin)
    if statut is not None:
        q = q.filter(Seance.statut == statut)
    seances = q.order_by(Seance.date.desc()).offset(offset).limit(limit).all()
    return _enrich(seances, db)


def get_by_id(seance_id: str, db: Session) -> Seance:
    s = db.query(Seance).filter(Seance.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Séance introuvable")
    return _enrich(s, db)


def create(data: SeanceCreate, db: Session) -> Seance:
    seance_data = data.model_dump(exclude={"employe_ids"})
    seance = Seance(id=str(uuid.uuid4()), **seance_data)
    db.add(seance)
    db.flush()

    for emp_id in (data.employe_ids or []):
        db.add(SeanceEmploye(seance_id=seance.id, employe_id=emp_id))

    db.commit()
    db.refresh(seance)
    # Si la séance est terminée (faite), prolonger de 4 semaines si créneaux automatiques
    if seance.statut == StatutSeanceEnum.faite and seance.patient_id:
        try:
            from app.services import planning_service
            planning_service.check_and_extend_creneaux_auto(seance.patient_id, db)
        except Exception:
            pass
    return _enrich(seance, db)


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
    return _enrich(seance, db)


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
        if existing.mode_generation == ModeGenerationEnum.auto:
            try:
                from app.services import planning_service
                from datetime import timedelta
                today = date_type.today()
                debut = max(existing.date_debut, today)
                fin = debut + timedelta(days=existing.horizon_jours or 28)
                if existing.date_fin:
                    fin = min(existing.date_fin, fin)
                planning_service.generer_creneaux_manuel(existing, debut, fin, db)
            except Exception:
                pass
        return existing

    planning = PatientPlanningRecurrent(id=str(uuid.uuid4()), patient_id=patient_id, **data.model_dump())
    db.add(planning)
    db.commit()
    db.refresh(planning)
    if planning.mode_generation == ModeGenerationEnum.auto:
        try:
            from app.services import planning_service
            from datetime import timedelta
            today = date_type.today()
            debut = max(planning.date_debut, today)
            fin = debut + timedelta(days=planning.horizon_jours or 28)
            if planning.date_fin:
                fin = min(planning.date_fin, fin)
            planning_service.generer_creneaux_manuel(planning, debut, fin, db)
        except Exception:
            pass
    return planning
