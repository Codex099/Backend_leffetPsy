"""
Service MCP Agent IA — Logique métier des 6 User Stories.

Réutilise strictement access_control_service.py existant.
Aucune nouvelle règle d'accès n'est définie ici.
"""

import uuid
import hashlib
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.mcp_token import McpToken
from app.models.employee import Employee
from app.models.patient import Patient
from app.models.dossier_medical import DossierMedical
from app.models.seance import Seance
from app.models.plan_therapeutique import PlanTherapeutique, StatutPlanEnum
from app.models.etape_plan_therapeutique import EtapePlanTherapeutique, StatutEtapeEnum
from app.schemas.mcp import McpPlanCreate, McpPlanUpdate, McpEtapeUpdate
from app.services.access_control_service import check_patient_access


# ─── Hachage token ───────────────────────────────────────────────────────────

def _hash_token(raw: str) -> str:
    """SHA-256 du token brut (déterministe, sans sel — le token est déjà cryptographiquement fort)."""
    return hashlib.sha256(raw.encode()).hexdigest()


# ─── US1 : Gestion des tokens MCP ────────────────────────────────────────────

def create_mcp_token(employee_id: str, nom: str, db: Session) -> dict:
    """
    Génère un nouveau token MCP personnel pour un employé.
    Retourne le token en clair (à afficher une seule fois) + les métadonnées.
    """
    if not nom or not nom.strip():
        raise HTTPException(status_code=422, detail="Le nom du token ne peut pas être vide")

    raw_token = str(uuid.uuid4())
    token_hash = _hash_token(raw_token)

    mcp_token = McpToken(
        id=str(uuid.uuid4()),
        employee_id=employee_id,
        token_hash=token_hash,
        nom=nom.strip(),
    )
    db.add(mcp_token)
    db.commit()
    db.refresh(mcp_token)

    return {
        "id": mcp_token.id,
        "nom": mcp_token.nom,
        "created_at": mcp_token.created_at,
        "token": raw_token,  # affiché une seule fois
    }


def list_mcp_tokens(employee_id: str, db: Session) -> List[McpToken]:
    """Liste tous les tokens (actifs et révoqués) d'un employé."""
    return (
        db.query(McpToken)
        .filter(McpToken.employee_id == employee_id)
        .order_by(McpToken.created_at.desc())
        .all()
    )


def revoke_mcp_token(token_id: str, employee_id: str, db: Session) -> None:
    """
    Révoque un token MCP (marque revoked_at).
    Seul le propriétaire peut révoquer son propre token.
    """
    token = (
        db.query(McpToken)
        .filter(McpToken.id == token_id, McpToken.employee_id == employee_id)
        .first()
    )
    if not token:
        raise HTTPException(status_code=404, detail="Token introuvable")
    if token.revoked_at is not None:
        raise HTTPException(status_code=409, detail="Ce token est déjà révoqué")
    token.revoked_at = datetime.now(timezone.utc)
    db.commit()


def verify_mcp_token(raw_token: str, db: Session) -> Employee:
    """
    Résout un raw token MCP → Employee.
    Lève 401 si le token est invalide, inconnu ou révoqué.
    """
    token_hash = _hash_token(raw_token)
    mcp_token = (
        db.query(McpToken)
        .filter(McpToken.token_hash == token_hash)
        .first()
    )
    if not mcp_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token MCP invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if mcp_token.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token MCP révoqué",
            headers={"WWW-Authenticate": "Bearer"},
        )
    employee = db.query(Employee).filter(Employee.id == mcp_token.employee_id).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Employé associé introuvable")
    return employee


# ─── US2 : Rechercher un patient + dossier médical ───────────────────────────

def search_patients(query: str, employee: Employee, db: Session) -> List[Patient]:
    """
    Recherche des patients par nom ou prénom (insensible à la casse).
    Respecte le périmètre d'accès de l'employé via access_control_service.
    """
    if not query or len(query.strip()) < 2:
        raise HTTPException(status_code=422, detail="La recherche doit comporter au moins 2 caractères")

    q = db.query(Patient)

    # Filtrage accès : admin voit tout, sinon uniquement les patients assignés
    if employee.role != "admin":
        from app.models.employee_patient_access import EmployeePatientAccess
        accessible_ids = [
            r.patient_id
            for r in db.query(EmployeePatientAccess.patient_id)
            .filter(EmployeePatientAccess.employee_id == employee.id)
            .all()
        ]
        q = q.filter(Patient.id.in_(accessible_ids))

    term = f"%{query.strip()}%"
    q = q.filter(
        or_(
            Patient.nom.ilike(term),
            Patient.prenom.ilike(term),
        )
    )
    return q.order_by(Patient.nom, Patient.prenom).limit(20).all()


def get_dossier_patient(patient_id: str, employee: Employee, db: Session) -> dict:
    """
    Retourne le patient + son dossier médical enrichi pour l'agent IA.
    Vérifie l'accès via check_patient_access.
    """
    patient = check_patient_access(patient_id, employee, db)
    dossier = db.query(DossierMedical).filter(DossierMedical.patient_id == patient_id).first()
    return {"patient": patient, "dossier": dossier}


# ─── US3 : Historique des séances ────────────────────────────────────────────

def get_seances_patient(
    patient_id: str,
    employee: Employee,
    db: Session,
    limit: int = 20,
) -> List[Seance]:
    """
    Retourne l'historique des séances d'un patient (plus récentes en premier).
    Respecte le contrôle d'accès existant.
    """
    check_patient_access(patient_id, employee, db)
    return (
        db.query(Seance)
        .filter(Seance.patient_id == patient_id)
        .order_by(Seance.date.desc())
        .limit(limit)
        .all()
    )


# ─── US4 : Lister plans thérapeutiques + statut étapes ───────────────────────

def list_plans_with_etapes(
    patient_id: str,
    employee: Employee,
    db: Session,
    statut: Optional[StatutPlanEnum] = None,
) -> List[PlanTherapeutique]:
    """
    Liste les plans thérapeutiques d'un patient avec leurs étapes et statuts.
    Filtrage optionnel par statut du plan.
    """
    check_patient_access(patient_id, employee, db)
    q = db.query(PlanTherapeutique).filter(PlanTherapeutique.patient_id == patient_id)
    if statut:
        q = q.filter(PlanTherapeutique.statut == statut)
    return q.order_by(PlanTherapeutique.date_debut.desc().nullslast()).all()


# ─── US5 : Créer un plan thérapeutique avec ses étapes ───────────────────────

def create_plan_with_etapes(
    patient_id: str,
    data: McpPlanCreate,
    employee: Employee,
    db: Session,
) -> PlanTherapeutique:
    """
    Crée un plan thérapeutique complet avec ses étapes en une seule transaction.
    Utilisé par l'agent IA après validation explicite du psychologue.
    """
    check_patient_access(patient_id, employee, db)

    if not data.titre or not data.titre.strip():
        raise HTTPException(status_code=422, detail="Le titre du plan ne peut pas être vide")

    # Valider le statut
    try:
        statut_enum = StatutPlanEnum(data.statut)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Statut invalide : {data.statut}")

    plan = PlanTherapeutique(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        titre=data.titre.strip(),
        statut=statut_enum,
        date_debut=data.date_debut,
        date_fin=data.date_fin,
        cree_par=employee.id,
    )
    db.add(plan)
    db.flush()  # obtenir plan.id avant d'insérer les étapes

    for etape_data in data.etapes:
        if not etape_data.titre or not etape_data.titre.strip():
            db.rollback()
            raise HTTPException(status_code=422, detail="Le titre d'une étape ne peut pas être vide")

        etape = EtapePlanTherapeutique(
            id=str(uuid.uuid4()),
            plan_id=plan.id,
            titre=etape_data.titre.strip(),
            description=etape_data.description,
            statut=etape_data.statut,
            ordre=etape_data.ordre,
            cree_par=employee.id,
        )
        db.add(etape)

    db.commit()
    db.refresh(plan)
    return plan


# ─── US6 : Modifier un plan ou une étape ─────────────────────────────────────

def update_plan_mcp(
    plan_id: str,
    data: McpPlanUpdate,
    employee: Employee,
    db: Session,
) -> PlanTherapeutique:
    """Modifie le titre, statut ou dates d'un plan thérapeutique via MCP."""
    plan = db.query(PlanTherapeutique).filter(PlanTherapeutique.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan thérapeutique introuvable")

    check_patient_access(plan.patient_id, employee, db)

    updates = data.model_dump(exclude_unset=True)
    if "statut" in updates:
        try:
            updates["statut"] = StatutPlanEnum(updates["statut"])
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Statut invalide : {updates['statut']}")

    for field, value in updates.items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    return plan


def update_etape_mcp(
    plan_id: str,
    etape_id: str,
    data: McpEtapeUpdate,
    employee: Employee,
    db: Session,
) -> EtapePlanTherapeutique:
    """Modifie une étape d'un plan thérapeutique via MCP."""
    plan = db.query(PlanTherapeutique).filter(PlanTherapeutique.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan thérapeutique introuvable")

    check_patient_access(plan.patient_id, employee, db)

    etape = (
        db.query(EtapePlanTherapeutique)
        .filter(
            EtapePlanTherapeutique.id == etape_id,
            EtapePlanTherapeutique.plan_id == plan_id,
        )
        .first()
    )
    if not etape:
        raise HTTPException(status_code=404, detail="Étape introuvable")

    updates = data.model_dump(exclude_unset=True)
    if "statut" in updates:
        try:
            updates["statut"] = StatutEtapeEnum(updates["statut"])
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Statut étape invalide : {updates['statut']}")

    for field, value in updates.items():
        setattr(etape, field, value)

    db.commit()
    db.refresh(etape)
    return etape
