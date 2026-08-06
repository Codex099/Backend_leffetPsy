import uuid
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentUpdate


def get_all(db: Session, limit: int = 100, offset: int = 0) -> List[Parent]:
    return db.query(Parent).offset(offset).limit(limit).all()


def get_by_id(parent_id: str, db: Session) -> Parent:
    p = db.query(Parent).filter(Parent.id == parent_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent introuvable")
    return p


def _check_telephone_unique(telephone: str, db: Session, exclude_id: str | None = None) -> None:
    """
    Vérifie qu'aucun autre parent n'utilise déjà ce numéro de téléphone.
    Lève un 409 Conflict si doublon détecté.
    """
    query = db.query(Parent).filter(Parent.telephone == telephone)
    if exclude_id:
        query = query.filter(Parent.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un parent avec ce numéro de téléphone existe déjà.",
        )


def create(data: ParentCreate, db: Session) -> Parent:
    _check_telephone_unique(data.telephone, db)
    parent = Parent(id=str(uuid.uuid4()), **data.model_dump())
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def update(parent_id: str, data: ParentUpdate, db: Session) -> Parent:
    parent = get_by_id(parent_id, db)
    update_data = data.model_dump(exclude_unset=True)
    # Vérifier unicité seulement si le téléphone change
    if "telephone" in update_data and update_data["telephone"] != parent.telephone:
        _check_telephone_unique(update_data["telephone"], db, exclude_id=parent_id)
    for field, value in update_data.items():
        setattr(parent, field, value)
    db.commit()
    db.refresh(parent)
    return parent


def delete(parent_id: str, db: Session) -> None:
    parent = get_by_id(parent_id, db)
    db.delete(parent)
    db.commit()
