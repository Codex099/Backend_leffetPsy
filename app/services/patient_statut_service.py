"""
Service de gestion du statut actif / inactif des patients.

Logique métier :
  - Activation   → est_actif=True, date_reactivation=now(),
                    entrée "actif" dans patient_statut_historique
  - Désactivation → est_actif=False, date_desactivation=now(),
                    entrée "inactif" dans patient_statut_historique
  - note_degradation → champ libre saisi par le psychologue lors d'une
                        réactivation pour signaler une dégradation pendant
                        la période d'inactivité.
"""

import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.patient_statut_historique import PatientStatutHistorique, StatutPatientEnum
from app.schemas.patient import ChangerStatutRequest


def changer_statut(
    patient_id: str,
    data: ChangerStatutRequest,
    employee_id: str,
    db: Session,
) -> Patient:
    """
    Active ou désactive un patient.

    - Mise à jour des champs est_actif, date_desactivation / date_reactivation.
    - Création automatique d'une entrée dans patient_statut_historique.
    - La note_degradation est stockée dans l'entrée historique (pertinente à la réactivation).
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient introuvable")

    now = datetime.now(timezone.utc)

    if data.est_actif:
        # Réactivation
        patient.est_actif = True
        patient.date_reactivation = now
        nouveau_statut = StatutPatientEnum.actif
    else:
        # Désactivation
        patient.est_actif = False
        patient.date_desactivation = now
        nouveau_statut = StatutPatientEnum.inactif

    # Création de l'entrée d'historique
    entree = PatientStatutHistorique(
        id=str(uuid.uuid4()),
        patient_id=patient_id,
        statut=nouveau_statut,
        date_changement=now,
        change_par=employee_id,
        note_degradation=data.note_degradation if data.est_actif else None,
    )
    db.add(entree)
    db.commit()
    db.refresh(patient)
    return patient


def get_historique(patient_id: str, db: Session) -> List[PatientStatutHistorique]:
    """Retourne l'historique complet des changements de statut d'un patient, du plus récent au plus ancien."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient introuvable")

    return (
        db.query(PatientStatutHistorique)
        .filter(PatientStatutHistorique.patient_id == patient_id)
        .order_by(PatientStatutHistorique.date_changement.desc())
        .all()
    )


def update_note_degradation(
    patient_id: str,
    historique_id: str,
    note_degradation: str,
    db: Session,
) -> PatientStatutHistorique:
    """
    Ajoute ou modifie la note_degradation sur une entrée d'historique existante.
    """
    entree = (
        db.query(PatientStatutHistorique)
        .filter(
            PatientStatutHistorique.id == historique_id,
            PatientStatutHistorique.patient_id == patient_id,
        )
        .first()
    )
    if not entree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entrée d'historique introuvable",
        )
    entree.note_degradation = note_degradation
    db.commit()
    db.refresh(entree)
    return entree
