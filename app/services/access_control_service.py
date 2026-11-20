"""
Centralisation du contrôle d'accès aux données médicales.

Règle :
  - admin → accès à tous les patients (None = pas de filtre)
  - psychologue / éducatrice → uniquement les patients accessibles (via accès explicites
    + séances + groupes + plans thérapeutiques)

OPTIMISATION PERFORMANCE :
  - Requête SQL UNION unique au lieu de 5-7 requêtes séquentielles
  - Cache in-memory Python avec TTL 90s par employé (évite les recalculs répétés)
  - Invalidation ciblée sur mutation des accès
"""

import time
from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.patient import Patient


# ─── Cache in-memory simple ───────────────────────────────────────────────────
# Format : { employee_id_str: (patient_ids_list_or_None, timestamp_float) }
_access_cache: dict[str, tuple[list[str] | None, float]] = {}
_CACHE_TTL_SECONDS = 90  # secondes — délai avant recalcul


def _get_from_cache(employee_id: str) -> list[str] | None | bool:
    """
    Retourne la liste des IDs si le cache est frais, sinon False (cache manquant/expiré).
    Retourne None si l'entrée dit "accès total" (admin).
    """
    entry = _access_cache.get(str(employee_id))
    if entry is None:
        return False  # pas en cache
    cached_ids, cached_at = entry
    if time.monotonic() - cached_at > _CACHE_TTL_SECONDS:
        del _access_cache[str(employee_id)]
        return False  # expiré
    return cached_ids  # peut être None (admin) ou list


def _set_cache(employee_id: str, ids: list[str] | None) -> None:
    _access_cache[str(employee_id)] = (ids, time.monotonic())


def invalidate_access_cache(employee_id: str) -> None:
    """Appeler après modification des accès d'un employé."""
    _access_cache.pop(str(employee_id), None)


def clear_access_cache() -> None:
    """Vide tout le cache (ex: redémarrage, maintenance)."""
    _access_cache.clear()


# ─── Requête principale ───────────────────────────────────────────────────────

_UNION_QUERY = text("""
    SELECT DISTINCT patient_id FROM (
        -- 1. Accès explicites (table employee_patient_access)
        SELECT patient_id::text
          FROM employee_patient_access
         WHERE employee_id = :eid

        UNION

        -- 2. Séances individuelles assignées à l'employé
        SELECT s.patient_id::text
          FROM seance s
          JOIN seance_employe se ON se.seance_id = s.id
         WHERE se.employe_id = :eid
           AND s.patient_id IS NOT NULL

        UNION

        -- 3. Patients des séances de groupe animées par l'employé
        SELECT sgp.patient_id::text
          FROM seance_groupe_participant sgp
          JOIN seance_groupe sg ON sg.id = sgp.seance_groupe_id
         WHERE sg.employe_id = :eid
           AND sgp.patient_id IS NOT NULL

        UNION

        -- 4. Notes de groupe rédigées par l'employé
        SELECT patient_id::text
          FROM seance_groupe_participant
         WHERE redige_par = :eid
           AND patient_id IS NOT NULL

        UNION

        -- 5. Plans thérapeutiques assignés à l'employé
        SELECT patient_id::text
          FROM plan_therapeutique
         WHERE assigne_a = :eid
           AND patient_id IS NOT NULL

        UNION

        -- 6. Étapes de plans assignées à l'employé
        SELECT pt.patient_id::text
          FROM etape_plan_therapeutique e
          JOIN plan_therapeutique pt ON pt.id = e.plan_id
         WHERE e.assigne_a = :eid
           AND pt.patient_id IS NOT NULL

        UNION

        -- 7. Sous-étapes de plans assignées à l'employé
        SELECT pt.patient_id::text
          FROM sous_etape_plan_therapeutique se2
          JOIN etape_plan_therapeutique e2 ON e2.id = se2.etape_id
          JOIN plan_therapeutique pt ON pt.id = e2.plan_id
         WHERE se2.assigne_a = :eid
           AND pt.patient_id IS NOT NULL
    ) AS combined
    WHERE patient_id IS NOT NULL
""")


def get_accessible_patient_ids(employee: Employee, db: Session) -> list[str] | None:
    """
    Retourne la liste des patient_ids accessibles pour un employé.
    Retourne None si admin (= accès à tous les patients, pas de filtre WHERE).

    Optimisé :
      - Requête SQL UNION unique (au lieu de 5-7 requêtes séquentielles)
      - Cache in-memory TTL 90s pour éviter les recalculs inutiles
    """
    if employee.role == "admin":
        return None  # pas de filtre

    # Vérifier le cache
    cached = _get_from_cache(str(employee.id))
    if cached is not False:
        return cached  # type: ignore[return-value]

    # Exécuter la requête UNION optimisée
    try:
        result = db.execute(_UNION_QUERY, {"eid": str(employee.id)})
        ids = [str(row[0]) for row in result if row[0] is not None]
    except Exception:
        # Fallback silencieux : pas de filtre en cas d'erreur SQL inattendue
        ids = []

    _set_cache(str(employee.id), ids)
    return ids


def check_patient_access(patient_id: str, employee: Employee, db: Session) -> Patient:
    """
    Vérifie que l'employé a le droit d'accéder au patient donné.
    Retourne le patient si l'accès est autorisé, sinon lève une 403 ou 404.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient introuvable",
        )

    if employee.role == "admin":
        return patient

    accessible_ids = get_accessible_patient_ids(employee, db)
    if accessible_ids is not None and patient_id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès à ce patient non autorisé",
        )
    return patient
