import uuid
from datetime import date as date_type
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seance_groupe import SeanceGroupe
from app.models.seance_groupe_participant import SeanceGroupeParticipant
from app.schemas.seance_groupe import SeanceGroupeCreate, SeanceGroupeUpdate, ParticipantUpdate
from app.services import enrichment_service


def _enrich(target, db: Session):
    """
    Attache le groupe, l'animateur et les participants (patient imbriqué) :
    l'agenda et l'écran de compte-rendu affichent des noms, pas des UUID.
    Chargement par lot — 4 requêtes quel que soit le nombre de séances.
    """
    is_list = isinstance(target, (list, tuple))
    seances = [s for s in (target if is_list else [target]) if s is not None]
    if not seances:
        return target

    enrichment_service.attach_groupe(seances, db)
    enrichment_service.attach_employee(seances, db)

    participants = (
        db.query(SeanceGroupeParticipant)
        .filter(SeanceGroupeParticipant.seance_groupe_id.in_([s.id for s in seances]))
        .all()
    )
    enrichment_service.attach_patient(participants, db)
    par_seance = enrichment_service.group_by(
        participants, "seance_groupe_id", enrichment_service.participant_summary
    )
    for s in seances:
        s.participants = par_seance.get(s.id, [])
    return target


def get_all(
    db: Session,
    groupe_id: Optional[str] = None,
    employe_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    date: Optional[date_type] = None,
    date_debut: Optional[date_type] = None,
    date_fin: Optional[date_type] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[SeanceGroupe]:
    q = db.query(SeanceGroupe)
    if groupe_id is not None:
        q = q.filter(SeanceGroupe.groupe_id == groupe_id)
    if employe_id is not None:
        q = q.filter(SeanceGroupe.employe_id == employe_id)
    if patient_id is not None:
        # Séances auxquelles ce patient participe (écran fiche patient)
        seance_ids = (
            db.query(SeanceGroupeParticipant.seance_groupe_id)
            .filter(SeanceGroupeParticipant.patient_id == patient_id)
            .subquery()
        )
        q = q.filter(SeanceGroupe.id.in_(seance_ids))
    if date is not None:
        q = q.filter(SeanceGroupe.date == date)
    if date_debut is not None:
        q = q.filter(SeanceGroupe.date >= date_debut)
    if date_fin is not None:
        q = q.filter(SeanceGroupe.date <= date_fin)
    seances = q.order_by(SeanceGroupe.date.desc()).offset(offset).limit(limit).all()
    return _enrich(seances, db)


def get_by_id(seance_id: str, db: Session) -> SeanceGroupe:
    s = db.query(SeanceGroupe).filter(SeanceGroupe.id == seance_id).first()
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Séance de groupe introuvable")
    return s


def get_detail(seance_id: str, db: Session) -> SeanceGroupe:
    """Séance de groupe enrichie (groupe, animateur, participants) — écran détail."""
    return _enrich(get_by_id(seance_id, db), db)


def create(data: SeanceGroupeCreate, db: Session) -> SeanceGroupe:
    seance = SeanceGroupe(id=str(uuid.uuid4()), **data.model_dump())
    db.add(seance)
    db.commit()
    db.refresh(seance)
    return _enrich(seance, db)


def update(seance_id: str, data: SeanceGroupeUpdate, db: Session) -> SeanceGroupe:
    seance = get_by_id(seance_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(seance, field, value)
    db.commit()
    db.refresh(seance)
    return _enrich(seance, db)


def delete(seance_id: str, db: Session) -> None:
    seance = get_by_id(seance_id, db)
    db.delete(seance)
    db.commit()


def update_participant(
    seance_groupe_id: str,
    patient_id: str,
    data: ParticipantUpdate,
    employee_id: str,
    db: Session,
) -> SeanceGroupeParticipant:
    get_by_id(seance_groupe_id, db)
    participant = (
        db.query(SeanceGroupeParticipant)
        .filter(
            SeanceGroupeParticipant.seance_groupe_id == seance_groupe_id,
            SeanceGroupeParticipant.patient_id == patient_id,
        )
        .first()
    )
    if not participant:
        participant = SeanceGroupeParticipant(
            seance_groupe_id=seance_groupe_id,
            patient_id=patient_id,
        )
        db.add(participant)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(participant, field, value)
    participant.redige_par = employee_id
    db.commit()
    db.refresh(participant)
    return enrichment_service.attach_patient(participant, db)
