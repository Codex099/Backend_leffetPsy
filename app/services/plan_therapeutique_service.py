import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.plan_therapeutique import PlanTherapeutique, StatutPlanEnum
from app.models.etape_plan_therapeutique import EtapePlanTherapeutique, StatutEtapeEnum
from app.models.sous_etape_plan_therapeutique import SousEtapePlanTherapeutique
from app.models.tache import Tache, StatutTacheEnum, PrioriteTacheEnum
from app.schemas.plan_therapeutique import (
    EtapeCreate,
    EtapeUpdate,
    PlanTherapeutiqueCreate,
    PlanTherapeutiqueUpdate,
    SousEtapeCreate,
    SousEtapeUpdate,
)


# ─── Plans ────────────────────────────────────────────────────────────────────

def list_plans(patient_id: str, statut: Optional[StatutPlanEnum], db: Session) -> List[PlanTherapeutique]:
    """Liste tous les plans thérapeutiques d'un patient, filtrables par statut."""
    q = db.query(PlanTherapeutique).filter(PlanTherapeutique.patient_id == patient_id)
    if statut is not None:
        q = q.filter(PlanTherapeutique.statut == statut)
    return q.order_by(PlanTherapeutique.date_debut.desc().nullslast()).all()


def create_plan(patient_id: str, data: PlanTherapeutiqueCreate, employee_id: str, db: Session) -> PlanTherapeutique:
    """Crée un nouveau plan thérapeutique pour un patient."""
    plan = PlanTherapeutique(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        cree_par=employee_id,
        **data.model_dump(),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def get_plan_by_id(plan_id: str, db: Session) -> PlanTherapeutique:
    p = db.query(PlanTherapeutique).filter(PlanTherapeutique.id == plan_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan thérapeutique introuvable")
    return p


def update_plan(plan_id: str, data: PlanTherapeutiqueUpdate, db: Session) -> PlanTherapeutique:
    """Modifie le titre, statut, dates ou assigné d'un plan thérapeutique."""
    plan = get_plan_by_id(plan_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(plan_id: str, db: Session) -> None:
    """Supprime un plan et toutes ses étapes (cascade)."""
    plan = get_plan_by_id(plan_id, db)
    db.delete(plan)
    db.commit()


def assign_plan(plan_id: str, employee_id: Optional[str], propager: bool, db: Session) -> PlanTherapeutique:
    """Assigne un employé au plan complet, avec propagation optionnelle aux étapes et séances."""
    plan = get_plan_by_id(plan_id, db)
    plan.assigne_a = employee_id

    if propager:
        for etape in plan.etapes:
            etape.assigne_a = employee_id
            for sous_etape in etape.sous_etapes:
                sous_etape.assigne_a = employee_id

    db.commit()
    db.refresh(plan)
    return plan


# ─── Étapes ───────────────────────────────────────────────────────────────────

def add_etape(plan_id: str, data: EtapeCreate, employee_id: str, db: Session) -> EtapePlanTherapeutique:
    plan = get_plan_by_id(plan_id, db)
    # Si assigne_a n'est pas spécifié, hérite du plan
    assigne = data.assigne_a if data.assigne_a is not None else plan.assigne_a
    dump = data.model_dump()
    dump["assigne_a"] = assigne
    etape = EtapePlanTherapeutique(id=str(uuid.uuid4()), plan_id=plan_id, cree_par=employee_id, **dump)
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


def assign_etape(plan_id: str, etape_id: str, employee_id: Optional[str], propager: bool, db: Session) -> EtapePlanTherapeutique:
    """Assigne un employé à une étape spécifique, avec propagation optionnelle aux sous-étapes."""
    etape = get_etape(plan_id, etape_id, db)
    etape.assigne_a = employee_id

    if propager:
        for sous_etape in etape.sous_etapes:
            sous_etape.assigne_a = employee_id

    db.commit()
    db.refresh(etape)
    return etape


# ─── Sous-Étapes (Séances) ────────────────────────────────────────────────────

def add_sous_etape(plan_id: str, etape_id: str, data: SousEtapeCreate, employee_id: str, db: Session) -> SousEtapePlanTherapeutique:
    """Crée une sous-étape (séance) dans une étape donnée."""
    etape = get_etape(plan_id, etape_id, db)
    # Héritage d'assignation si non spécifiée
    assigne = data.assigne_a if data.assigne_a is not None else etape.assigne_a
    dump = data.model_dump()
    dump["assigne_a"] = assigne

    sous_etape = SousEtapePlanTherapeutique(
        id=str(uuid.uuid4()),
        etape_id=etape_id,
        cree_par=employee_id,
        **dump,
    )
    db.add(sous_etape)
    db.commit()
    db.refresh(sous_etape)
    return sous_etape


def get_sous_etape(plan_id: str, etape_id: str, sous_etape_id: str, db: Session) -> SousEtapePlanTherapeutique:
    get_etape(plan_id, etape_id, db)
    se = (
        db.query(SousEtapePlanTherapeutique)
        .filter(
            SousEtapePlanTherapeutique.id == sous_etape_id,
            SousEtapePlanTherapeutique.etape_id == etape_id,
        )
        .first()
    )
    if not se:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Séance/Sous-étape introuvable")
    return se


def update_sous_etape(
    plan_id: str,
    etape_id: str,
    sous_etape_id: str,
    data: SousEtapeUpdate,
    db: Session,
) -> SousEtapePlanTherapeutique:
    se = get_sous_etape(plan_id, etape_id, sous_etape_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(se, field, value)

    # Vérification automatique du statut de l'étape parente
    if data.statut is not None:
        etape = get_etape(plan_id, etape_id, db)
        all_sous_etapes = etape.sous_etapes
        if all_sous_etapes:
            all_done = all(
                (s.statut == StatutEtapeEnum.fait if s.id != se.id else data.statut == StatutEtapeEnum.fait)
                for s in all_sous_etapes
            )
            any_in_progress = any(
                (s.statut in (StatutEtapeEnum.en_cours, StatutEtapeEnum.fait) if s.id != se.id else data.statut in (StatutEtapeEnum.en_cours, StatutEtapeEnum.fait))
                for s in all_sous_etapes
            )
            if all_done:
                etape.statut = StatutEtapeEnum.fait
            elif any_in_progress and etape.statut == StatutEtapeEnum.a_faire:
                etape.statut = StatutEtapeEnum.en_cours

    db.commit()
    db.refresh(se)
    return se


def delete_sous_etape(plan_id: str, etape_id: str, sous_etape_id: str, db: Session) -> None:
    se = get_sous_etape(plan_id, etape_id, sous_etape_id, db)
    db.delete(se)
    db.commit()


def assign_sous_etape(
    plan_id: str,
    etape_id: str,
    sous_etape_id: str,
    employee_id: Optional[str],
    db: Session,
) -> SousEtapePlanTherapeutique:
    """Assigne un employé à une sous-étape (séance) spécifique."""
    se = get_sous_etape(plan_id, etape_id, sous_etape_id, db)
    se.assigne_a = employee_id
    db.commit()
    db.refresh(se)
    return se


# ─── Tâches ───────────────────────────────────────────────────────────────────

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
