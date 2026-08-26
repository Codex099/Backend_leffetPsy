"""
Tests MCP Agent IA — 6 User Stories.

Couvre :
  US1 — Génération / liste / révocation de token MCP
  US2 — Recherche patient + consultation dossier médical
  US3 — Historique des séances d'un patient
  US4 — Liste des plans thérapeutiques + statut étapes
  US5 — Création d'un plan avec ses étapes (transaction)
  US6 — Modification d'un plan et d'une étape

Cas d'erreur testés :
  - Token MCP invalide → 401
  - Token MCP révoqué → 401
  - Accès à un patient non assigné (via role educatrice) → 403
  - Patient inexistant → 404
  - Recherche trop courte → 422
  - Titre vide à la création → 422
  - Révocation d'un token déjà révoqué → 409

Exécution :
  .venv\\Scripts\\python.exe -m pytest test_mcp.py -v
"""

import sys
from datetime import date

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, Base, engine
from app.core.security import create_access_token, hash_password
from app.models.employee import Employee, RoleEmployeEnum
from app.models.patient import Patient, SexeEnum
from app.models.employee_patient_access import EmployeePatientAccess
from app.models.dossier_medical import DossierMedical
from app.models.seance import Seance, StatutSeanceEnum
from app.models.plan_therapeutique import PlanTherapeutique, StatutPlanEnum
from app.models.etape_plan_therapeutique import EtapePlanTherapeutique, StatutEtapeEnum
from app.models.mcp_token import McpToken

import uuid
import hashlib

client = TestClient(app)

# ─── Fixtures DB ─────────────────────────────────────────────────────────────

def _uuid(seed: str) -> str:
    """UUID reproductible à partir d'un seed (pour les tests)."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mcp-test-{seed}"))


ADMIN_ID    = _uuid("admin")
PSY_ID      = _uuid("psy")
EDU_ID      = _uuid("educatrice")
PATIENT_ID  = _uuid("patient")
PATIENT2_ID = _uuid("patient2")


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def setup_test_db():
    """Crée les données de test nécessaires et retourne les tokens JWT."""
    # S'assurer que la table mcp_tokens existe
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # ── Employés ────────────────────────────────────────────────────────
        if not db.query(Employee).filter(Employee.id == ADMIN_ID).first():
            db.add(Employee(
                id=ADMIN_ID, nom="Admin", prenom="MCP",
                telephone="0600000001", username="admin_mcp_test",
                password_hash=hash_password("pass"), role=RoleEmployeEnum.admin,
            ))

        if not db.query(Employee).filter(Employee.id == PSY_ID).first():
            db.add(Employee(
                id=PSY_ID, nom="Dupont", prenom="Claire",
                telephone="0600000002", username="psy_mcp_test",
                password_hash=hash_password("pass"), role=RoleEmployeEnum.psychologue,
            ))

        if not db.query(Employee).filter(Employee.id == EDU_ID).first():
            db.add(Employee(
                id=EDU_ID, nom="Martin", prenom="Sophie",
                telephone="0600000003", username="edu_mcp_test",
                password_hash=hash_password("pass"), role=RoleEmployeEnum.educatrice,
            ))

        # ── Patients ─────────────────────────────────────────────────────────
        if not db.query(Patient).filter(Patient.id == PATIENT_ID).first():
            db.add(Patient(
                id=PATIENT_ID, nom="Benali", prenom="Yassine",
                sexe=SexeEnum.masculin, date_naissance=date(2015, 3, 10), est_actif=True,
            ))

        if not db.query(Patient).filter(Patient.id == PATIENT2_ID).first():
            db.add(Patient(
                id=PATIENT2_ID, nom="Roudet", prenom="Emile",
                sexe=SexeEnum.masculin, date_naissance=date(2014, 7, 20), est_actif=True,
            ))

        db.flush()

        # ── Accès : psy → PATIENT uniquement (pas PATIENT2) ──────────────────
        if not db.query(EmployeePatientAccess).filter(
            EmployeePatientAccess.employee_id == PSY_ID,
            EmployeePatientAccess.patient_id == PATIENT_ID,
        ).first():
            db.add(EmployeePatientAccess(employee_id=PSY_ID, patient_id=PATIENT_ID))

        # ── Dossier médical ────────────────────────────────────────────────
        if not db.query(DossierMedical).filter(DossierMedical.patient_id == PATIENT_ID).first():
            db.add(DossierMedical(
                id=_uuid("dossier"),
                patient_id=PATIENT_ID,
                antecedents_medicaux="RAS",
                medicaments_pris="Aucun",
            ))

        # ── Séances de test ────────────────────────────────────────────────
        if not db.query(Seance).filter(Seance.id == _uuid("seance1")).first():
            db.add(Seance(
                id=_uuid("seance1"), patient_id=PATIENT_ID,
                date=date(2026, 8, 1), statut=StatutSeanceEnum.faite,
            ))
            db.add(Seance(
                id=_uuid("seance2"), patient_id=PATIENT_ID,
                date=date(2026, 8, 15), statut=StatutSeanceEnum.prevue,
            ))

        # ── Plan thérapeutique de test (US4) ──────────────────────────────
        if not db.query(PlanTherapeutique).filter(PlanTherapeutique.id == _uuid("plan1")).first():
            plan = PlanTherapeutique(
                id=_uuid("plan1"), patient_id=PATIENT_ID,
                titre="Plan test US4", statut=StatutPlanEnum.actif,
                cree_par=PSY_ID,
            )
            db.add(plan)
            db.flush()
            db.add(EtapePlanTherapeutique(
                id=_uuid("etape1"), plan_id=_uuid("plan1"),
                titre="Étape 1", statut=StatutEtapeEnum.a_faire, ordre=1, cree_par=PSY_ID,
            ))
            db.add(EtapePlanTherapeutique(
                id=_uuid("etape2"), plan_id=_uuid("plan1"),
                titre="Étape 2", statut=StatutEtapeEnum.en_cours, ordre=2, cree_par=PSY_ID,
            ))

        db.commit()

        # ── Tokens JWT ────────────────────────────────────────────────────
        admin_jwt = create_access_token({"sub": ADMIN_ID, "role": "admin"})
        psy_jwt   = create_access_token({"sub": PSY_ID,   "role": "psychologue"})
        edu_jwt   = create_access_token({"sub": EDU_ID,   "role": "educatrice"})

    finally:
        db.close()

    return admin_jwt, psy_jwt, edu_jwt


def cleanup_mcp_tokens(employee_id: str):
    """Supprime tous les tokens MCP de test d'un employé."""
    db = SessionLocal()
    try:
        db.query(McpToken).filter(McpToken.employee_id == employee_id).delete()
        db.commit()
    finally:
        db.close()


# ─── Tests US1 : Gestion des tokens MCP ──────────────────────────────────────

def test_us1_generate_token(psy_jwt):
    """US1 : Un psychologue peut générer un token MCP personnel."""
    headers = {"Authorization": f"Bearer {psy_jwt}"}
    res = client.post("/api/auth/mcp-token", json={"nom": "Claude Desktop"}, headers=headers)
    print(f"POST /api/auth/mcp-token: {res.status_code}")
    assert res.status_code == 201, res.text
    data = res.json()
    assert "token" in data, "Le token en clair doit être retourné à la création"
    assert "id" in data
    assert data["nom"] == "Claude Desktop"
    return data["token"]


def test_us1_list_tokens(psy_jwt):
    """US1 : Un psychologue peut lister ses tokens."""
    headers = {"Authorization": f"Bearer {psy_jwt}"}
    res = client.get("/api/auth/mcp-tokens", headers=headers)
    print(f"GET /api/auth/mcp-tokens: {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_us1_revoke_token(psy_jwt):
    """US1 : Un psychologue peut révoquer son token — il devient inutilisable."""
    headers = {"Authorization": f"Bearer {psy_jwt}"}

    # Génère un token dédié pour ce test
    res = client.post("/api/auth/mcp-token", json={"nom": "Token à révoquer"}, headers=headers)
    assert res.status_code == 201
    token_id   = res.json()["id"]
    raw_token  = res.json()["token"]
    mcp_headers = {"Authorization": f"Bearer {raw_token}"}

    # Le token fonctionne avant révocation
    res = client.get(f"/api/mcp/patients/search?q=Benali", headers=mcp_headers)
    print(f"GET /api/mcp/patients/search (avant révocation): {res.status_code}")
    assert res.status_code == 200

    # Révocation
    res = client.delete(f"/api/auth/mcp-tokens/{token_id}", headers=headers)
    print(f"DELETE /api/auth/mcp-tokens/{token_id}: {res.status_code}")
    assert res.status_code == 204

    # Le token révoqué → 401
    res = client.get(f"/api/mcp/patients/search?q=Benali", headers=mcp_headers)
    print(f"GET /api/mcp/patients/search (après révocation): {res.status_code}")
    assert res.status_code == 401

    # Double révocation → 409
    res = client.delete(f"/api/auth/mcp-tokens/{token_id}", headers=headers)
    print(f"DELETE /api/auth/mcp-tokens/{token_id} (2ème fois): {res.status_code}")
    assert res.status_code == 409


def test_us1_invalid_token():
    """US1 : Un token MCP invalide retourne 401."""
    headers = {"Authorization": "Bearer totalement-invalide-uuid"}
    res = client.get("/api/mcp/patients/search?q=test", headers=headers)
    print(f"GET /api/mcp/patients/search (token invalide): {res.status_code}")
    assert res.status_code == 401


def test_us1_nom_vide(psy_jwt):
    """US1 : Générer un token avec un nom vide → 422."""
    headers = {"Authorization": f"Bearer {psy_jwt}"}
    res = client.post("/api/auth/mcp-token", json={"nom": "   "}, headers=headers)
    print(f"POST /api/auth/mcp-token (nom vide): {res.status_code}")
    assert res.status_code in (422, 400), res.text


# ─── Tests US2 : Recherche patient + dossier médical ─────────────────────────

def test_us2_search_patient(mcp_token):
    """US2 : Recherche d'un patient par nom."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get("/api/mcp/patients/search?q=Benali", headers=headers)
    print(f"GET /api/mcp/patients/search?q=Benali: {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    results = res.json()
    assert len(results) >= 1
    assert any(p["nom"] == "Benali" for p in results)


def test_us2_search_too_short(mcp_token):
    """US2 : Recherche avec moins de 2 caractères → 422."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get("/api/mcp/patients/search?q=B", headers=headers)
    print(f"GET /api/mcp/patients/search?q=B: {res.status_code}")
    assert res.status_code == 422


def test_us2_search_inaccessible_patient(mcp_token):
    """US2 : Le psychologue ne voit pas les patients hors périmètre (PATIENT2)."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get("/api/mcp/patients/search?q=Roudet", headers=headers)
    print(f"GET /api/mcp/patients/search?q=Roudet (hors périmètre): {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    # PATIENT2 ne doit pas apparaître dans les résultats du psychologue
    assert not any(p["id"] == PATIENT2_ID for p in res.json())


def test_us2_get_dossier(mcp_token):
    """US2 : Consultation du dossier médical d'un patient accessible."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT_ID}/dossier", headers=headers)
    print(f"GET /api/mcp/patients/{PATIENT_ID}/dossier: {res.status_code}")
    assert res.status_code == 200
    data = res.json()
    assert "patient" in data
    assert data["patient"]["id"] == PATIENT_ID
    assert "dossier" in data


def test_us2_dossier_patient_inexistant(mcp_token):
    """US2 : Dossier d'un patient inexistant → 404."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get("/api/mcp/patients/patient-qui-nexiste-pas/dossier", headers=headers)
    print(f"GET /api/mcp/patients/inexistant/dossier: {res.status_code}")
    assert res.status_code == 404


def test_us2_dossier_patient_non_autorise(mcp_token):
    """US2 : Accès au dossier d'un patient hors périmètre → 403."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT2_ID}/dossier", headers=headers)
    print(f"GET /api/mcp/patients/PATIENT2/dossier (non autorisé): {res.status_code}")
    assert res.status_code == 403


# ─── Tests US3 : Historique des séances ──────────────────────────────────────

def test_us3_list_seances(mcp_token):
    """US3 : Liste des séances d'un patient accessible."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT_ID}/seances", headers=headers)
    print(f"GET /api/mcp/patients/{PATIENT_ID}/seances: {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    assert len(res.json()) >= 2


def test_us3_seances_limit(mcp_token):
    """US3 : Le paramètre limit est respecté."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT_ID}/seances?limit=1", headers=headers)
    print(f"GET /api/mcp/patients/{PATIENT_ID}/seances?limit=1: {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    assert len(res.json()) <= 1


def test_us3_seances_patient_non_autorise(mcp_token):
    """US3 : Séances d'un patient hors périmètre → 403."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT2_ID}/seances", headers=headers)
    print(f"GET /api/mcp/patients/PATIENT2/seances (non autorisé): {res.status_code}")
    assert res.status_code == 403


# ─── Tests US4 : Liste des plans thérapeutiques ───────────────────────────────

def test_us4_list_plans(mcp_token):
    """US4 : Liste des plans avec leurs étapes."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT_ID}/plans", headers=headers)
    print(f"GET /api/mcp/patients/{PATIENT_ID}/plans: {res.status_code}, count={len(res.json())}")
    assert res.status_code == 200
    plans = res.json()
    assert len(plans) >= 1
    # Vérifier que les étapes sont incluses
    plan = next((p for p in plans if p["id"] == _uuid("plan1")), None)
    assert plan is not None
    assert "etapes" in plan
    assert len(plan["etapes"]) == 2


def test_us4_list_plans_filtre_statut(mcp_token):
    """US4 : Filtrage par statut du plan."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT_ID}/plans?statut=actif", headers=headers)
    print(f"GET /api/mcp/patients/{PATIENT_ID}/plans?statut=actif: {res.status_code}")
    assert res.status_code == 200
    for plan in res.json():
        assert plan["statut"] == "actif"


def test_us4_plans_patient_non_autorise(mcp_token):
    """US4 : Plans d'un patient hors périmètre → 403."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.get(f"/api/mcp/patients/{PATIENT2_ID}/plans", headers=headers)
    print(f"GET /api/mcp/patients/PATIENT2/plans (non autorisé): {res.status_code}")
    assert res.status_code == 403


# ─── Tests US5 : Créer un plan avec ses étapes ───────────────────────────────

def test_us5_create_plan_with_etapes(mcp_token):
    """US5 : Création d'un plan complet avec étapes en une requête."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    payload = {
        "titre": "Plan IA créé via MCP",
        "statut": "actif",
        "date_debut": "2026-09-01",
        "etapes": [
            {"titre": "Évaluation initiale", "ordre": 1, "statut": "a_faire"},
            {"titre": "Travail sur l'anxiété", "ordre": 2, "statut": "a_faire"},
            {"titre": "Consolidation", "ordre": 3, "statut": "a_faire"},
        ],
    }
    res = client.post(f"/api/mcp/patients/{PATIENT_ID}/plans", json=payload, headers=headers)
    print(f"POST /api/mcp/patients/{PATIENT_ID}/plans: {res.status_code}")
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["titre"] == "Plan IA créé via MCP"
    assert len(data["etapes"]) == 3
    return data["id"]


def test_us5_create_plan_titre_vide(mcp_token):
    """US5 : Création d'un plan avec titre vide → 422."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    payload = {"titre": "   ", "etapes": []}
    res = client.post(f"/api/mcp/patients/{PATIENT_ID}/plans", json=payload, headers=headers)
    print(f"POST /api/mcp/patients/{PATIENT_ID}/plans (titre vide): {res.status_code}")
    assert res.status_code in (422, 400)


def test_us5_create_plan_patient_non_autorise(mcp_token):
    """US5 : Création d'un plan pour un patient hors périmètre → 403."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    payload = {"titre": "Plan non autorisé", "etapes": []}
    res = client.post(f"/api/mcp/patients/{PATIENT2_ID}/plans", json=payload, headers=headers)
    print(f"POST /api/mcp/patients/PATIENT2/plans (non autorisé): {res.status_code}")
    assert res.status_code == 403


def test_us5_create_plan_statut_invalide(mcp_token):
    """US5 : Statut invalide → 422."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    payload = {"titre": "Plan valide", "statut": "inexistant", "etapes": []}
    res = client.post(f"/api/mcp/patients/{PATIENT_ID}/plans", json=payload, headers=headers)
    print(f"POST /api/mcp/patients/{PATIENT_ID}/plans (statut invalide): {res.status_code}")
    assert res.status_code in (422, 400)


# ─── Tests US6 : Modifier un plan ou une étape ───────────────────────────────

def test_us6_update_plan(mcp_token):
    """US6 : Modification d'un plan existant."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id = _uuid("plan1")

    res = client.patch(f"/api/mcp/plans/{plan_id}", json={"titre": "Titre modifié MCP"}, headers=headers)
    print(f"PATCH /api/mcp/plans/{plan_id}: {res.status_code}")
    assert res.status_code == 200, res.text
    assert res.json()["titre"] == "Titre modifié MCP"


def test_us6_update_plan_statut(mcp_token):
    """US6 : Modification du statut d'un plan."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id = _uuid("plan1")

    res = client.patch(f"/api/mcp/plans/{plan_id}", json={"statut": "suspendu"}, headers=headers)
    print(f"PATCH /api/mcp/plans/{plan_id} statut=suspendu: {res.status_code}")
    assert res.status_code == 200
    assert res.json()["statut"] == "suspendu"

    # Remettre actif
    client.patch(f"/api/mcp/plans/{plan_id}", json={"statut": "actif"}, headers=headers)


def test_us6_update_plan_statut_invalide(mcp_token):
    """US6 : Statut invalide lors d'une modification → 422."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id = _uuid("plan1")

    res = client.patch(f"/api/mcp/plans/{plan_id}", json={"statut": "mauvais_statut"}, headers=headers)
    print(f"PATCH /api/mcp/plans/{plan_id} (statut invalide): {res.status_code}")
    assert res.status_code in (422, 400)


def test_us6_update_plan_inexistant(mcp_token):
    """US6 : Modifier un plan inexistant → 404."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    res = client.patch("/api/mcp/plans/plan-inexistant-uuid", json={"titre": "test"}, headers=headers)
    print(f"PATCH /api/mcp/plans/inexistant: {res.status_code}")
    assert res.status_code == 404


def test_us6_update_etape(mcp_token):
    """US6 : Modification d'une étape (statut + titre)."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id  = _uuid("plan1")
    etape_id = _uuid("etape1")

    res = client.patch(
        f"/api/mcp/plans/{plan_id}/etapes/{etape_id}",
        json={"statut": "en_cours", "titre": "Étape 1 modifiée"},
        headers=headers,
    )
    print(f"PATCH /api/mcp/plans/{plan_id}/etapes/{etape_id}: {res.status_code}")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["statut"] == "en_cours"
    assert data["titre"] == "Étape 1 modifiée"


def test_us6_update_etape_statut_invalide(mcp_token):
    """US6 : Statut étape invalide → 422."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id  = _uuid("plan1")
    etape_id = _uuid("etape1")

    res = client.patch(
        f"/api/mcp/plans/{plan_id}/etapes/{etape_id}",
        json={"statut": "invalide"},
        headers=headers,
    )
    print(f"PATCH étape (statut invalide): {res.status_code}")
    assert res.status_code in (422, 400)


def test_us6_update_etape_inexistante(mcp_token):
    """US6 : Modifier une étape inexistante → 404."""
    headers = {"Authorization": f"Bearer {mcp_token}"}
    plan_id = _uuid("plan1")

    res = client.patch(
        f"/api/mcp/plans/{plan_id}/etapes/etape-inexistante",
        json={"titre": "test"},
        headers=headers,
    )
    print(f"PATCH étape inexistante: {res.status_code}")
    assert res.status_code == 404


# ─── Point d'entrée principal ─────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("TEST MCP Agent IA -- 6 User Stories")
    print("=" * 60)

    admin_jwt, psy_jwt, edu_jwt = setup_test_db()
    psy_headers = {"Authorization": f"Bearer {psy_jwt}"}

    # Nettoyer les tokens MCP de test precedents
    cleanup_mcp_tokens(PSY_ID)

    # -- US1 ------------------------------------------------------------------
    print("\n[US1] Tokens API MCP")
    raw_token = test_us1_generate_token(psy_jwt)
    test_us1_list_tokens(psy_jwt)
    test_us1_revoke_token(psy_jwt)
    test_us1_invalid_token()
    test_us1_nom_vide(psy_jwt)

    # Generer un token de travail pour les US suivantes
    res = client.post("/api/auth/mcp-token", json={"nom": "Token principal test"}, headers=psy_headers)
    assert res.status_code == 201
    mcp_token = res.json()["token"]

    # -- US2 ------------------------------------------------------------------
    print("\n[US2] Recherche patient + dossier medical")
    test_us2_search_patient(mcp_token)
    test_us2_search_too_short(mcp_token)
    test_us2_search_inaccessible_patient(mcp_token)
    test_us2_get_dossier(mcp_token)
    test_us2_dossier_patient_inexistant(mcp_token)
    test_us2_dossier_patient_non_autorise(mcp_token)

    # -- US3 ------------------------------------------------------------------
    print("\n[US3] Historique des seances")
    test_us3_list_seances(mcp_token)
    test_us3_seances_limit(mcp_token)
    test_us3_seances_patient_non_autorise(mcp_token)

    # -- US4 ------------------------------------------------------------------
    print("\n[US4] Liste des plans therapeutiques")
    test_us4_list_plans(mcp_token)
    test_us4_list_plans_filtre_statut(mcp_token)
    test_us4_plans_patient_non_autorise(mcp_token)

    # -- US5 ------------------------------------------------------------------
    print("\n[US5] Creation plan + etapes")
    test_us5_create_plan_with_etapes(mcp_token)
    test_us5_create_plan_titre_vide(mcp_token)
    test_us5_create_plan_patient_non_autorise(mcp_token)
    test_us5_create_plan_statut_invalide(mcp_token)

    # -- US6 ------------------------------------------------------------------
    print("\n[US6] Modification plan / etape")
    test_us6_update_plan(mcp_token)
    test_us6_update_plan_statut(mcp_token)
    test_us6_update_plan_statut_invalide(mcp_token)
    test_us6_update_plan_inexistant(mcp_token)
    test_us6_update_etape(mcp_token)
    test_us6_update_etape_statut_invalide(mcp_token)
    test_us6_update_etape_inexistante(mcp_token)

    print("\n" + "=" * 60)
    print("TOUS LES TESTS MCP PASSENT !")
    print("=" * 60)
