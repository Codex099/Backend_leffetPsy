import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tache import Tache, StatutTacheEnum
from app.schemas.tache import TacheCreate, TacheUpdate
from app.services import enrichment_service


def _enrich(target, db: Session):
    """Attache le patient concerné et l'employé assigné (affichés sur la carte)."""
    enrichment_service.attach_patient(target, db)
    enrichment_service.attach_employee(target, db, fk_attr="assigne_a", key="assigne_employee")
    return target


def get_all(
    employee,
    db: Session,
    assigne_a_moi: Optional[bool] = None,
    statut: Optional[StatutTacheEnum] = None,
    patient_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Tache]:
    q = db.query(Tache)
    # Un non-admin ne voit que ses tâches : la restriction reste prioritaire.
    if employee.role != "admin":
        q = q.filter(Tache.assigne_a == employee.id)
    elif assigne_a_moi:
        q = q.filter(Tache.assigne_a == employee.id)
    if statut is not None:
        q = q.filter(Tache.statut == statut)
    if patient_id is not None:
        q = q.filter(Tache.patient_id == patient_id)
    taches = q.offset(offset).limit(limit).all()
    return _enrich(taches, db)


def get_by_id(tache_id: str, db: Session) -> Tache:
    t = db.query(Tache).filter(Tache.id == tache_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    return _enrich(t, db)


def create(data: TacheCreate, employee, db: Session) -> Tache:
    assigne_a = data.assigne_a
    # Seul l'administrateur peut assigner des tâches à d'autres employés
    if employee.role != "admin":
        if assigne_a and assigne_a != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul l'administrateur peut assigner des tâches à d'autres employés",
            )
        assigne_a = employee.id

    tache_data = data.model_dump()
    tache_data["assigne_a"] = assigne_a
    tache = Tache(id=str(uuid.uuid4()), cree_par=employee.id, **tache_data)
    db.add(tache)
    db.commit()
    db.refresh(tache)
    return _enrich(tache, db)


def update(tache_id: str, data: TacheUpdate, employee, db: Session) -> Tache:
    tache = get_by_id(tache_id, db)
    if employee.role != "admin":
        if tache.assigne_a != employee.id and tache.cree_par != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès à cette tâche non autorisé",
            )
        if data.assigne_a is not None and data.assigne_a != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seul l'administrateur peut assigner des tâches à d'autres employés",
            )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tache, field, value)
    db.commit()
    db.refresh(tache)
    return _enrich(tache, db)


def delete(tache_id: str, employee, db: Session) -> None:
    tache = get_by_id(tache_id, db)
    if employee.role != "admin":
        if tache.cree_par != employee.id and tache.assigne_a != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez pas supprimer cette tâche",
            )
    db.delete(tache)
    db.commit()
