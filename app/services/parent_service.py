import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.models.patient_parent import PatientParent
from app.models.patient import Patient
from app.schemas.parent import ParentCreate, ParentUpdate


def get_all(db: Session, search: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Parent]:
    q = db.query(Parent)
    if search:
        motif = f"%{search.strip()}%"
        q = q.filter(or_(
            Parent.nom.ilike(motif),
            Parent.prenom.ilike(motif),
            Parent.telephone.ilike(motif),
        ))
    return q.order_by(Parent.nom, Parent.prenom).offset(offset).limit(limit).all()


def get_by_id(parent_id: str, db: Session) -> Parent:
    p = db.query(Parent).filter(Parent.id == parent_id).first()
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent introuvable")
    return p


def get_by_telephone(telephone: str, db: Session) -> Optional[Parent]:
    return db.query(Parent).filter(Parent.telephone == telephone.strip()).first()


def _check_telephone_unique(telephone: str, db: Session, exclude_id: str | None = None) -> None:
    query = db.query(Parent).filter(Parent.telephone == telephone.strip())
    if exclude_id:
        query = query.filter(Parent.id != exclude_id)
    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un parent avec ce numéro de téléphone existe déjà ({existing.prenom} {existing.nom}).",
        )


def create(data: ParentCreate, db: Session, find_existing: bool = False) -> Parent:
    existing = get_by_telephone(data.telephone, db)
    if existing:
        if find_existing:
            return existing
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un parent avec ce numéro de téléphone existe déjà ({existing.prenom} {existing.nom}).",
            headers={"X-Existing-Parent-Id": existing.id},
        )
    parent = Parent(id=str(uuid.uuid4()), **data.model_dump())
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def update(parent_id: str, data: ParentUpdate, db: Session) -> Parent:
    parent = get_by_id(parent_id, db)
    update_data = data.model_dump(exclude_unset=True)
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


def get_patients_for_parent(parent_id: str, employee, db: Session) -> list:
    from app.services.access_control_service import get_accessible_patient_ids
    get_by_id(parent_id, db)
    accessible_ids = get_accessible_patient_ids(employee, db)
    rows = db.query(PatientParent).filter(PatientParent.parent_id == parent_id).all()
    res = []
    for r in rows:
        if accessible_ids is not None and r.patient_id not in accessible_ids:
            continue
        pat = db.query(Patient).filter(Patient.id == r.patient_id).first()
        if pat:
            res.append({
                "patient_id": pat.id,
                "nom": pat.nom,
                "prenom": pat.prenom,
                "role": r.role,
                "est_actif": pat.est_actif,
                "date_naissance": pat.date_naissance.isoformat() if pat.date_naissance else None,
                "photo": pat.photo,
            })
    return res
