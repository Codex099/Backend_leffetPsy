from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee, require_roles
from app.models.plan_therapeutique import StatutPlanEnum
from app.schemas.plan_therapeutique import (
    PlanTherapeutiqueCreate,
    PlanTherapeutiqueUpdate,
    PlanTherapeutiqueResponse,
    EtapeCreate,
    EtapeUpdate,
    EtapeResponse,
    SousEtapeCreate,
    SousEtapeUpdate,
    SousEtapeResponse,
    AssignerRequest,
    CreerTacheDepuisEtapeRequest,
)
from app.schemas.tache import TacheResponse
from app.services import plan_therapeutique_service
from app.services.access_control_service import check_patient_access

router = APIRouter(tags=["Plans Thérapeutiques"])

admin_only = require_roles("admin")
staff_only = get_current_employee


# ─── Plans (multi-plans par patient) ─────────────────────────────────────────

@router.get("/api/patients/{patient_id}/plans-therapeutiques", response_model=List[PlanTherapeutiqueResponse])
def list_plans(
    patient_id: str,
    statut: Optional[StatutPlanEnum] = None,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Liste tous les plans thérapeutiques d'un patient."""
    check_patient_access(patient_id, employee, db)
    return plan_therapeutique_service.list_plans(patient_id, statut, db)


@router.post(
    "/api/patients/{patient_id}/plans-therapeutiques",
    response_model=PlanTherapeutiqueResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    patient_id: str,
    data: PlanTherapeutiqueCreate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Crée un nouveau plan thérapeutique pour le patient."""
    check_patient_access(patient_id, employee, db)
    return plan_therapeutique_service.create_plan(patient_id, data, employee.id, db)


@router.get("/api/plans-therapeutiques/{plan_id}", response_model=PlanTherapeutiqueResponse)
def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Consulte un plan thérapeutique et ses étapes/séances."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan


@router.put("/api/plans-therapeutiques/{plan_id}", response_model=PlanTherapeutiqueResponse)
@router.patch("/api/plans-therapeutiques/{plan_id}", response_model=PlanTherapeutiqueResponse)
def update_plan(
    plan_id: str,
    data: PlanTherapeutiqueUpdate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Modifie le titre, statut, dates ou assigné d'un plan thérapeutique."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.update_plan(plan_id, data, db)


@router.delete("/api/plans-therapeutiques/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    employee=Depends(admin_only),
):
    """Supprime un plan et toutes ses étapes. Réservé aux admins."""
    plan_therapeutique_service.get_plan_by_id(plan_id, db)
    plan_therapeutique_service.delete_plan(plan_id, db)


@router.post("/api/plans-therapeutiques/{plan_id}/assigner", response_model=PlanTherapeutiqueResponse)
def assign_plan(
    plan_id: str,
    data: AssignerRequest,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Assigne un employé au plan complet, avec propagation optionnelle aux étapes et séances."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.assign_plan(plan_id, data.employee_id, data.propager, db)


# ─── Étapes ───────────────────────────────────────────────────────────────────

@router.get("/api/plans-therapeutiques/{plan_id}/etapes", response_model=List[EtapeResponse])
def list_etapes(
    plan_id: str,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Liste les étapes d'un plan."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan.etapes


@router.post(
    "/api/plans-therapeutiques/{plan_id}/etapes",
    response_model=EtapeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_etape(
    plan_id: str,
    data: EtapeCreate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Ajoute une étape à un plan thérapeutique."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.add_etape(plan_id, data, employee.id, db)


@router.put("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}", response_model=EtapeResponse)
@router.patch("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}", response_model=EtapeResponse)
def update_etape(
    plan_id: str,
    etape_id: str,
    data: EtapeUpdate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Modifie une étape de plan thérapeutique."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.update_etape(plan_id, etape_id, data, db)


@router.delete("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etape(
    plan_id: str,
    etape_id: str,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Supprime une étape de plan."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    plan_therapeutique_service.delete_etape(plan_id, etape_id, db)


@router.post("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/assigner", response_model=EtapeResponse)
def assign_etape(
    plan_id: str,
    etape_id: str,
    data: AssignerRequest,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Assigne un employé à une étape spécifique, avec propagation optionnelle aux sous-étapes."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.assign_etape(plan_id, etape_id, data.employee_id, data.propager, db)


# ─── Sous-Étapes (Séances) ────────────────────────────────────────────────────

@router.post(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/sous-etapes",
    response_model=SousEtapeResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_sous_etape(
    plan_id: str,
    etape_id: str,
    data: SousEtapeCreate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Ajoute une sous-étape (séance) avec la description de ce qui doit être fait."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.add_sous_etape(plan_id, etape_id, data, employee.id, db)


@router.put(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/sous-etapes/{sous_etape_id}",
    response_model=SousEtapeResponse,
)
@router.patch(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/sous-etapes/{sous_etape_id}",
    response_model=SousEtapeResponse,
)
def update_sous_etape(
    plan_id: str,
    etape_id: str,
    sous_etape_id: str,
    data: SousEtapeUpdate,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Modifie une sous-étape (statut, titre, description séance, date, assigné)."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.update_sous_etape(plan_id, etape_id, sous_etape_id, data, db)


@router.delete(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/sous-etapes/{sous_etape_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_sous_etape(
    plan_id: str,
    etape_id: str,
    sous_etape_id: str,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Supprime une sous-étape (séance)."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    plan_therapeutique_service.delete_sous_etape(plan_id, etape_id, sous_etape_id, db)


@router.post(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/sous-etapes/{sous_etape_id}/assigner",
    response_model=SousEtapeResponse,
)
def assign_sous_etape(
    plan_id: str,
    etape_id: str,
    sous_etape_id: str,
    data: AssignerRequest,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Assigne un employé à une sous-étape (séance) spécifique."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.assign_sous_etape(plan_id, etape_id, sous_etape_id, data.employee_id, db)


# ─── Tâches ───────────────────────────────────────────────────────────────────

@router.post(
    "/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/creer-tache",
    response_model=TacheResponse,
    status_code=status.HTTP_201_CREATED,
)
def creer_tache_depuis_etape(
    plan_id: str,
    etape_id: str,
    data: CreerTacheDepuisEtapeRequest,
    db: Session = Depends(get_db),
    employee=Depends(staff_only),
):
    """Crée une tâche assignée à un employé depuis une étape de plan."""
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.creer_tache_depuis_etape(plan_id, etape_id, data.assigne_a, employee.id, db)
