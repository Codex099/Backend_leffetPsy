from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_roles
from app.schemas.plan_therapeutique import (
    PlanTherapeutiqueResponse,
    EtapeCreate,
    EtapeUpdate,
    EtapeResponse,
    CreerTacheDepuisEtapeRequest,
)
from app.schemas.tache import TacheResponse
from app.services import plan_therapeutique_service
from app.services.access_control_service import check_patient_access

router = APIRouter(tags=["Plans Thérapeutiques"])

# Restreint aux psychologues et admins
psychologue_or_admin = require_roles("psychologue", "admin")


@router.get("/api/patients/{patient_id}/plan-therapeutique", response_model=PlanTherapeutiqueResponse)
def get_or_create_plan(
    patient_id: str,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    check_patient_access(patient_id, employee, db)
    return plan_therapeutique_service.get_or_create_plan(patient_id, employee.id, db)


@router.post("/api/plans-therapeutiques/{plan_id}/etapes", response_model=EtapeResponse, status_code=status.HTTP_201_CREATED)
def add_etape(
    plan_id: str,
    data: EtapeCreate,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.add_etape(plan_id, data, employee.id, db)


@router.put("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}", response_model=EtapeResponse)
def update_etape(
    plan_id: str,
    etape_id: str,
    data: EtapeUpdate,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.update_etape(plan_id, etape_id, data, db)


@router.delete("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_etape(
    plan_id: str,
    etape_id: str,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    plan_therapeutique_service.delete_etape(plan_id, etape_id, db)


@router.post("/api/plans-therapeutiques/{plan_id}/etapes/{etape_id}/creer-tache", response_model=TacheResponse, status_code=status.HTTP_201_CREATED)
def creer_tache_depuis_etape(
    plan_id: str,
    etape_id: str,
    data: CreerTacheDepuisEtapeRequest,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    plan = plan_therapeutique_service.get_plan_by_id(plan_id, db)
    check_patient_access(plan.patient_id, employee, db)
    return plan_therapeutique_service.creer_tache_depuis_etape(plan_id, etape_id, data.assigne_a, employee.id, db)
