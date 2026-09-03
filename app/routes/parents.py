from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee, require_admin
from app.schemas.parent import ParentCreate, ParentUpdate, ParentResponse
from app.services import parent_service

router = APIRouter(prefix="/api/parents", tags=["Parents"])


@router.get("", response_model=List[ParentResponse])
def list_parents(
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """Liste les parents. Paramètres optionnels : ?search=nom, prénom ou téléphone, ?limit=100, ?offset=0."""
    return parent_service.get_all(db, search=search, limit=limit, offset=offset)


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def create_parent(
    data: ParentCreate,
    find_existing: bool = False,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    return parent_service.create(data, db, find_existing=find_existing)


@router.get("/by-phone/{telephone}", response_model=ParentResponse)
def get_parent_by_phone(telephone: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    parent = parent_service.get_by_telephone(telephone, db)
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent introuvable pour ce numéro")
    return parent


@router.get("/{parent_id}/patients")
def get_parent_patients(parent_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return parent_service.get_patients_for_parent(parent_id, employee, db)


@router.get("/{parent_id}", response_model=ParentResponse)
def get_parent(parent_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return parent_service.get_by_id(parent_id, db)


@router.put("/{parent_id}", response_model=ParentResponse)
@router.patch("/{parent_id}", response_model=ParentResponse)
def update_parent(parent_id: str, data: ParentUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return parent_service.update(parent_id, data, db)


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(parent_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    parent_service.delete(parent_id, db)
