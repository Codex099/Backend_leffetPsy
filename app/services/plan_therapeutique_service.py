import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.plan_therapeutique import PlanTherapeutique
from app.models.etape_plan_therapeutique import EtapePlanTherapeutique
from app.models.tache import Tache, StatutTacheEnum, PrioriteTacheEnum
from app.schemas.plan_therapeutique import EtapeCreate, EtapeUpdate


def get_or_create_plan(patient_id: str, employee_id: str, db: Session) -> PlanTherapeutique:
    plan = db.query(PlanTherapeutique).filter(PlanTherapeutique.patient_id == patient_id).first()
    if not plan:
        plan = PlanTherapeutique(id=str(uuid.uuid4()), patient_id=patient_id, cree_par=employee_id)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan


def get_plan_by_id(plan_id: str, db: Session) -> PlanTherapeutique:
    p = db.query(PlanTherapeutique).filter(PlanTherapeutique.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan thérapeutique introuvable")
    return p


def add_etape(plan_id: str, data: EtapeCreate, employee_id: str, db: Session) -> EtapePlanTherapeutique:
    get_plan_by_id(plan_id, db)
    etape = EtapePlanTherapeutique(id=str(uuid.uuid4()), plan_id=plan_id, cree_par=employee_id, **data.model_dump())
    db.add(etape)
    db.commit()
    db.refresh(etape)
    return etape


def get_etape(plan_id: str, etape_id: str, db: Session) -> EtapePlanTherapeutique:
    etape = (
        db.query(EtapePlanTherapeutique)
        .filter(EtapePlanTherapeutique.id == etape_id, EtapePlanTherapeutique.plan_id == plan_id)
        .first()
    )
    if not etape:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Étape introuvable")
    return etape


def update_etape(plan_id: str, etape_id: str, data: EtapeUpdate, db: Session) -> EtapePlanTherapeutique:
    etape = get_etape(plan_id, etape_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(etape, field, value)
    db.commit()
    db.refresh(etape)
    return etape


def delete_etape(plan_id: str, etape_id: str, db: Session) -> None:
    etape = get_etape(plan_id, etape_id, db)
    db.delete(etape)
    db.commit()


def creer_tache_depuis_etape(plan_id: str, etape_id: str, assigne_a: str, employee_id: str, db: Session) -> Tache:
    etape = get_etape(plan_id, etape_id, db)
    plan = get_plan_by_id(plan_id, db)
    tache = Tache(
        id=str(uuid.uuid4()),
        titre=etape.titre,
        description=etape.description,
        assigne_a=assigne_a,
        cree_par=employee_id,
        patient_id=plan.patient_id,
        etape_plan_id=etape.id,
        statut=StatutTacheEnum.a_faire,
        priorite=PrioriteTacheEnum.normale,
    )
    db.add(tache)
    db.commit()
    db.refresh(tache)
    return tache
