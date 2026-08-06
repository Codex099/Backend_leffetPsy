import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tache import Tache
from app.schemas.tache import TacheCreate, TacheUpdate


def get_all(employee, db: Session, limit: int = 100, offset: int = 0) -> List[Tache]:
    q = db.query(Tache)
    if employee.role != "admin":
        q = q.filter(Tache.assigne_a == employee.id)
    return q.offset(offset).limit(limit).all()


def get_by_id(tache_id: str, db: Session) -> Tache:
    t = db.query(Tache).filter(Tache.id == tache_id).first()
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tâche introuvable")
    return t


def create(data: TacheCreate, employee_id: str, db: Session) -> Tache:
    tache = Tache(id=str(uuid.uuid4()), cree_par=employee_id, **data.model_dump())
    db.add(tache)
    db.commit()
    db.refresh(tache)
    return tache


def update(tache_id: str, data: TacheUpdate, db: Session) -> Tache:
    tache = get_by_id(tache_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(tache, field, value)
    db.commit()
    db.refresh(tache)
    return tache


def delete(tache_id: str, db: Session) -> None:
    tache = get_by_id(tache_id, db)
    db.delete(tache)
    db.commit()
