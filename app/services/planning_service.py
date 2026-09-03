"""
Service de génération des créneaux récurrents pour les séances individuelles.

Modes :
  - auto  : appelé par le scheduler APScheduler toutes les 24h pour tous les plannings actifs.
  - manuel: déclenché via la route POST /patients/{id}/planning-recurrent/generer
            pour une période date_debut → date_fin donnée.

Logique :
  - Pour chaque planning actif, on génère des séances pour les jours de la semaine
    configurés, entre [date_debut, min(date_fin_planning, horizon)].
  - Une séance n'est créée QUE si elle n'existe pas déjà (unicité patient_id + date +
    heure_debut pour éviter les doublons).
"""

import uuid
import logging
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.patient_planning_recurrent import PatientPlanningRecurrent, ModeGenerationEnum
from app.models.seance import Seance, StatutSeanceEnum
from app.models.seance_employe import SeanceEmploye
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Mapping nom de jour → weekday Python (lundi=0, dimanche=6)
JOUR_TO_WEEKDAY = {
    "lundi": 0,
    "mardi": 1,
    "mercredi": 2,
    "jeudi": 3,
    "vendredi": 4,
    "samedi": 5,
    "dimanche": 6,
}


def _generate_slots(
    planning: PatientPlanningRecurrent,
    date_debut: date,
    date_fin: date,
    db: Session,
) -> int:
    """Génère les séances manquantes pour un planning entre date_debut et date_fin."""
    jours_cibles = {
        JOUR_TO_WEEKDAY[j.lower()]
        for j in (planning.jours_semaine or [])
        if j.lower() in JOUR_TO_WEEKDAY
    }

    created = 0
    current = date_debut
    while current <= date_fin:
        if current.weekday() in jours_cibles:
            # Vérifier doublon
            existing = (
                db.query(Seance)
                .filter(
                    Seance.patient_id == planning.patient_id,
                    Seance.date == current,
                    Seance.heure_debut == planning.heure_debut,
                )
                .first()
            )
            if not existing:
                seance = Seance(
                    id=str(uuid.uuid4()),
                    patient_id=planning.patient_id,
                    date=current,
                    heure_debut=planning.heure_debut,
                    heure_fin=planning.heure_fin,
                    statut=StatutSeanceEnum.prevue,
                )
                db.add(seance)
                db.flush()

                # Assigner le psychologue par défaut si configuré
                if planning.employe_id:
                    db.add(SeanceEmploye(seance_id=seance.id, employe_id=planning.employe_id))
                created += 1
        current += timedelta(days=1)

    db.commit()
    return created


def generer_creneaux_manuel(
    planning: PatientPlanningRecurrent,
    date_debut: date,
    date_fin: date,
    db: Session,
) -> int:
    """Génération manuelle pour une période donnée (déclenchée par route API)."""
    return _generate_slots(planning, date_debut, date_fin, db)



def check_and_extend_creneaux_auto(patient_id: str, db: Session) -> int:
    """
    Si le planning est en mode 'auto', vérifie si la séance finale ou presque finale
    du créneau actuel est atteinte (séances futures <= 1 ou dernière séance dans <= 7 jours).
    Génère alors automatiquement un nouveau créneau de 4 semaines (28 jours)
    à partir du lendemain de la dernière séance.
    """
    planning = (
        db.query(PatientPlanningRecurrent)
        .filter(
            PatientPlanningRecurrent.patient_id == patient_id,
            PatientPlanningRecurrent.mode_generation == ModeGenerationEnum.auto,
        )
        .first()
    )
    if not planning:
        return 0

    today = date.today()
    if planning.date_fin and planning.date_fin < today:
        return 0

    derniere_seance = (
        db.query(Seance)
        .filter(Seance.patient_id == patient_id)
        .order_by(Seance.date.desc())
        .first()
    )

    futures_prevues = (
        db.query(Seance)
        .filter(
            Seance.patient_id == patient_id,
            Seance.date >= today,
            Seance.statut == StatutSeanceEnum.prevue,
        )
        .count()
    )

    horizon_jours = planning.horizon_jours or 28
    # Si fin de créneau (0 ou 1 séance restante, ou dernière séance passée/aujourd'hui)
    if futures_prevues <= 1 or not derniere_seance or derniere_seance.date <= today:
        start_date = (derniere_seance.date + timedelta(days=1)) if (derniere_seance and derniere_seance.date >= today) else today
        end_date = start_date + timedelta(days=horizon_jours)
        if planning.date_fin:
            end_date = min(planning.date_fin, end_date)
        if start_date <= end_date:
            created = _generate_slots(planning, start_date, end_date, db)
            logger.info(f"[AutoPlanning] {created} créneaux de 4 semaines générés pour le patient {patient_id}")
            return created
    return 0

def run_auto_generation() -> None:
    """
    Tâche planifiée (APScheduler) : génère les créneaux pour tous les plannings
    en mode `auto` qui sont encore actifs.
    """
    db: Session = SessionLocal()
    try:
        today = date.today()
        plannings = (
            db.query(PatientPlanningRecurrent)
            .filter(PatientPlanningRecurrent.mode_generation == ModeGenerationEnum.auto)
            .all()
        )
        total = 0
        for p in plannings:
            if p.date_fin and p.date_fin < today:
                continue  # planning terminé
            horizon = today + timedelta(days=p.horizon_jours or 28)
            fin = min(p.date_fin, horizon) if p.date_fin else horizon
            debut = max(p.date_debut, today)
            if debut <= fin:
                total += _generate_slots(p, debut, fin, db)
        logger.info(f"[AutoPlanning] {total} créneaux générés pour {len(plannings)} plannings")
    except Exception as exc:
        logger.error(f"[AutoPlanning] Erreur : {exc}")
        db.rollback()
    finally:
        db.close()
