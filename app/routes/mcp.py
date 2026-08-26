"""
Routes MCP Agent IA — 6 User Stories.

Authentification : Bearer <mcp_token_personnel>
Rôles autorisés : psychologue, admin

Routes de gestion des tokens (auth JWT classique) :
  POST   /api/auth/mcp-token           — US1 : générer un token
  GET    /api/auth/mcp-tokens          — US1 : lister mes tokens
  DELETE /api/auth/mcp-tokens/{id}     — US1 : révoquer un token

Routes MCP (auth MCP token) :
  GET    /api/mcp/patients/search             — US2 : rechercher un patient
  GET    /api/mcp/patients/{id}/dossier       — US2 : dossier médical
  GET    /api/mcp/patients/{id}/seances       — US3 : historique séances
  GET    /api/mcp/patients/{id}/plans         — US4 : liste plans + étapes
  POST   /api/mcp/patients/{id}/plans         — US5 : créer plan + étapes
  PATCH  /api/mcp/plans/{plan_id}             — US6 : modifier plan
  PATCH  /api/mcp/plans/{plan_id}/etapes/{id} — US6 : modifier étape
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import (
    get_current_employee,
    get_current_employee_from_mcp_token,
    require_mcp_roles,
)
from app.models.plan_therapeutique import StatutPlanEnum
from app.schemas.mcp import (
    McpTokenCreate,
    McpTokenResponse,
    McpTokenListItem,
    McpPlanCreate,
    McpPlanUpdate,
    McpEtapeUpdate,
)
from app.schemas.plan_therapeutique import PlanTherapeutiqueResponse, EtapeResponse
from app.schemas.patient import PatientResponse
from app.schemas.seance import SeanceResponse
from app.schemas.dossier_medical import DossierMedicalResponse
from app.services import mcp_service

router = APIRouter(tags=["MCP Agent IA"])

# Dependency : routes MCP accessibles aux psychologues et admins via token MCP
mcp_psy_or_admin = require_mcp_roles("psychologue", "admin")


# ─── US1 : Gestion des tokens API personnels ─────────────────────────────────
# Ces routes utilisent l'auth JWT classique (pas le token MCP)

@router.post(
    "/api/auth/mcp-token",
    response_model=McpTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="US1 — Générer un token API MCP personnel",
    description=(
        "Génère un token API MCP personnel pour l'employé connecté. "
        "Le token en clair est affiché **une seule fois** dans la réponse. "
        "Stockez-le dans Claude Desktop ou votre connecteur MCP. "
        "**Auth** : JWT session classique."
    ),
)
def create_mcp_token(
    data: McpTokenCreate,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    return mcp_service.create_mcp_token(employee.id, data.nom, db)


@router.get(
    "/api/auth/mcp-tokens",
    response_model=List[McpTokenListItem],
    summary="US1 — Lister mes tokens MCP",
    description="Retourne tous les tokens MCP de l'employé connecté (actifs et révoqués). **Auth** : JWT session.",
)
def list_mcp_tokens(
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    return mcp_service.list_mcp_tokens(employee.id, db)


@router.delete(
    "/api/auth/mcp-tokens/{token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="US1 — Révoquer un token MCP",
    description="Révoque un token MCP personnel (marque `revoked_at`). **Auth** : JWT session.",
)
def revoke_mcp_token(
    token_id: str,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    mcp_service.revoke_mcp_token(token_id, employee.id, db)


# ─── US2 : Rechercher un patient + dossier médical ───────────────────────────

@router.get(
    "/api/mcp/patients/search",
    response_model=List[PatientResponse],
    summary="US2 — Rechercher un patient (MCP)",
    description=(
        "Recherche des patients par nom ou prénom. "
        "Respecte le périmètre d'accès de l'employé. "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def search_patients(
    q: str = Query(..., min_length=2, description="Terme de recherche (nom ou prénom)"),
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    return mcp_service.search_patients(q, employee, db)


@router.get(
    "/api/mcp/patients/{patient_id}/dossier",
    summary="US2 — Consulter le dossier médical d'un patient (MCP)",
    description=(
        "Retourne le patient avec son dossier médical complet. "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def get_dossier_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    result = mcp_service.get_dossier_patient(patient_id, employee, db)
    patient_data = PatientResponse.model_validate(result["patient"])
    dossier_data = (
        DossierMedicalResponse.model_validate(result["dossier"])
        if result["dossier"]
        else None
    )
    return {"patient": patient_data, "dossier": dossier_data}


# ─── US3 : Historique des séances ────────────────────────────────────────────

@router.get(
    "/api/mcp/patients/{patient_id}/seances",
    response_model=List[SeanceResponse],
    summary="US3 — Historique des séances d'un patient (MCP)",
    description=(
        "Retourne les séances d'un patient triées par date décroissante. "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def get_seances_patient(
    patient_id: str,
    limit: int = Query(default=20, ge=1, le=100, description="Nombre maximum de séances à retourner"),
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    seances = mcp_service.get_seances_patient(patient_id, employee, db, limit=limit)
    return [SeanceResponse.model_validate(s) for s in seances]


# ─── US4 : Lister plans thérapeutiques + statut étapes ───────────────────────

@router.get(
    "/api/mcp/patients/{patient_id}/plans",
    response_model=List[PlanTherapeutiqueResponse],
    summary="US4 — Lister les plans thérapeutiques d'un patient (MCP)",
    description=(
        "Retourne les plans thérapeutiques avec leurs étapes et statuts. "
        "Filtrage optionnel par statut du plan. "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def list_plans_mcp(
    patient_id: str,
    statut: Optional[StatutPlanEnum] = Query(default=None, description="Filtrer par statut : actif|archive|suspendu"),
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    plans = mcp_service.list_plans_with_etapes(patient_id, employee, db, statut=statut)
    return [PlanTherapeutiqueResponse.model_validate(p) for p in plans]


# ─── US5 : Créer un plan thérapeutique avec ses étapes ───────────────────────

@router.post(
    "/api/mcp/patients/{patient_id}/plans",
    response_model=PlanTherapeutiqueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="US5 — Créer un plan thérapeutique complet (MCP)",
    description=(
        "Crée un plan thérapeutique avec toutes ses étapes en une seule requête. "
        "À utiliser après validation explicite du psychologue. "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def create_plan_mcp(
    patient_id: str,
    data: McpPlanCreate,
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    plan = mcp_service.create_plan_with_etapes(patient_id, data, employee, db)
    return PlanTherapeutiqueResponse.model_validate(plan)


# ─── US6 : Modifier un plan ou une étape ─────────────────────────────────────

@router.patch(
    "/api/mcp/plans/{plan_id}",
    response_model=PlanTherapeutiqueResponse,
    summary="US6 — Modifier un plan thérapeutique (MCP)",
    description=(
        "Modifie le titre, statut ou dates d'un plan thérapeutique. "
        "Seuls les champs fournis sont modifiés (PATCH sémantique). "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def update_plan_mcp(
    plan_id: str,
    data: McpPlanUpdate,
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    plan = mcp_service.update_plan_mcp(plan_id, data, employee, db)
    return PlanTherapeutiqueResponse.model_validate(plan)


@router.patch(
    "/api/mcp/plans/{plan_id}/etapes/{etape_id}",
    response_model=EtapeResponse,
    summary="US6 — Modifier une étape d'un plan (MCP)",
    description=(
        "Modifie le titre, description, statut ou ordre d'une étape. "
        "Seuls les champs fournis sont modifiés (PATCH sémantique). "
        "**Auth** : Bearer token MCP personnel."
    ),
)
def update_etape_mcp(
    plan_id: str,
    etape_id: str,
    data: McpEtapeUpdate,
    db: Session = Depends(get_db),
    employee=Depends(mcp_psy_or_admin),
):
    etape = mcp_service.update_etape_mcp(plan_id, etape_id, data, employee, db)
    return EtapeResponse.model_validate(etape)
