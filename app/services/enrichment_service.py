"""
Enrichissement des réponses API — architecture backend-driven.

Le PRD impose que l'application mobile ne contienne aucune logique métier :
elle affiche ce que l'API lui envoie. Les réponses doivent donc porter les
objets liés (patient, employé, groupe…) et pas seulement leurs identifiants,
sinon l'app affiche « Patient #<uuid> » au lieu du nom.

Les objets liés sont attachés comme attributs sur les instances ORM : les
schémas Pydantic sont en `from_attributes = True` et lisent donc directement
`obj.patient`. Aucun modèle ne déclare de `relationship()` vers ces tables,
il n'y a donc pas de collision de nom.

Deux règles à respecter en ajoutant un résumé ici :
  1. chargement par lot (`WHERE id IN (...)`) pour éviter les N+1 sur les
     listes paginées ;
  2. valeurs JSON-safe uniquement (`jsonable`) — les champs cibles sont typés
     `Optional[Any]` dans les schémas, Pydantic ne les convertit donc pas.
"""

import enum
from datetime import date, datetime, time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.groupe import Groupe
from app.models.groupe_planning_recurrent import GroupePlanningRecurrent
from app.models.patient import Patient
from app.models.seance_groupe_participant import SeanceGroupeParticipant


# ─── Conversion JSON-safe ──────────────────────────────────────────────────────

def jsonable(value: Any) -> Any:
    """Convertit enums / dates / heures en primitives sérialisables."""
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


# ─── Résumés d'entités liées ───────────────────────────────────────────────────

def patient_summary(p: Optional[Patient]) -> Optional[dict]:
    """Résumé patient affiché dans les listes (agenda, tâches, groupes…)."""
    if p is None:
        return None
    return {
        "id": p.id,
        "nom": p.nom,
        "prenom": p.prenom,
        "sexe": jsonable(p.sexe),
        "date_naissance": jsonable(p.date_naissance),
        "photo": p.photo,
        "est_actif": p.est_actif,
    }


def employee_summary(e: Optional[Employee]) -> Optional[dict]:
    """Résumé employé — jamais de password_hash."""
    if e is None:
        return None
    return {
        "id": e.id,
        "nom": e.nom,
        "prenom": e.prenom,
        "telephone": e.telephone,
        "role": jsonable(e.role),
    }


def groupe_summary(g: Optional[Groupe]) -> Optional[dict]:
    if g is None:
        return None
    return {
        "id": g.id,
        "nom": g.nom,
        "type_planning": jsonable(g.type_planning),
        "description": g.description,
    }


def groupe_planning_summary(p: Optional[GroupePlanningRecurrent]) -> Optional[dict]:
    """Créneau fixe d'un groupe (US planning récurrent de groupe)."""
    if p is None:
        return None
    return {
        "id": p.id,
        "groupe_id": p.groupe_id,
        "jour_semaine": jsonable(p.jour_semaine),
        "heure_debut": jsonable(p.heure_debut),
        "heure_fin": jsonable(p.heure_fin),
    }


def participant_summary(p: Optional[SeanceGroupeParticipant]) -> Optional[dict]:
    """
    Résumé participant d'une séance de groupe, patient imbriqué compris.
    `attach_patient` doit avoir été appliqué avant pour que `patient` soit peuplé.
    """
    if p is None:
        return None
    return {
        "seance_groupe_id": p.seance_groupe_id,
        "patient_id": p.patient_id,
        "statut_presence": jsonable(p.statut_presence),
        "description_etat": p.description_etat,
        "reponses_questionnaire": p.reponses_questionnaire,
        "medias": p.medias,
        "redige_par": p.redige_par,
        "patient": getattr(p, "patient", None),
    }


# ─── Attachement par lot ───────────────────────────────────────────────────────

def _attach(target, db: Session, model, summary, fk_attr: str, key: str):
    """
    Charge en une requête les objets référencés par `fk_attr` et les attache
    sous `key`. Accepte un objet seul ou une liste ; retourne `target` (muté).
    """
    is_list = isinstance(target, (list, tuple))
    rows = [r for r in (target if is_list else [target]) if r is not None]
    if not rows:
        return target

    ids = {getattr(r, fk_attr, None) for r in rows}
    ids.discard(None)

    by_id: dict = {}
    if ids:
        for obj in db.query(model).filter(model.id.in_(ids)).all():
            by_id[obj.id] = summary(obj)

    for r in rows:
        setattr(r, key, by_id.get(getattr(r, fk_attr, None)))
    return target


def attach_patient(target, db: Session, fk_attr: str = "patient_id", key: str = "patient"):
    return _attach(target, db, Patient, patient_summary, fk_attr, key)


def attach_employee(target, db: Session, fk_attr: str = "employe_id", key: str = "employe"):
    return _attach(target, db, Employee, employee_summary, fk_attr, key)


def attach_groupe(target, db: Session, fk_attr: str = "groupe_id", key: str = "groupe"):
    return _attach(target, db, Groupe, groupe_summary, fk_attr, key)


def group_by(rows, fk_attr: str, summary) -> dict:
    """
    Regroupe des lignes par clé étrangère en appliquant `summary` à chacune.
    Utilisé pour attacher des collections (patients d'un groupe, participants
    d'une séance) après un chargement par lot unique.
    """
    grouped: dict = {}
    for r in rows:
        item = summary(r)
        if item is not None:
            grouped.setdefault(getattr(r, fk_attr), []).append(item)
    return grouped


def linked(key: str):
    """
    Résumé pour une table de liaison : renvoie simplement l'objet déjà attaché
    sous `key`. Permet de passer `linked("patient")` à `group_by` pour aplatir
    patient_groupe → liste de patients.
    """
    def _summary(link):
        return getattr(link, key, None)
    return _summary
