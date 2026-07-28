import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentUpdate


def get_all(db: Session) -> List[Parent]:
    return db.query(Parent).all()


def get_by_id(parent_id: str, db: Session) -> Parent:
    p = db.query(Parent).filter(Parent.id == parent_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent introuvable")
    return p


def create(data: ParentCreate, db: Session) -> Parent:
    parent = Parent(id=str(uuid.uuid4()), **data.model_dump())
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def update(parent_id: str, data: ParentUpdate, db: Session) -> Parent:
    parent = get_by_id(parent_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(parent, field, value)
    db.commit()
    db.refresh(parent)
    return parent


def delete(parent_id: str, db: Session) -> None:
    parent = get_by_id(parent_id, db)
    db.delete(parent)
    db.commit()
