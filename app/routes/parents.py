from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee, require_admin
from app.schemas.parent import ParentCreate, ParentUpdate, ParentResponse
from app.services import parent_service

router = APIRouter(prefix="/api/parents", tags=["Parents"])


@router.get("", response_model=List[ParentResponse])
def list_parents(limit: int = 100, offset: int = 0, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return parent_service.get_all(db, limit=limit, offset=offset)


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
def create_parent(data: ParentCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return parent_service.create(data, db)


@router.get("/{parent_id}", response_model=ParentResponse)
def get_parent(parent_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return parent_service.get_by_id(parent_id, db)


@router.put("/{parent_id}", response_model=ParentResponse)
def update_parent(parent_id: str, data: ParentUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return parent_service.update(parent_id, data, db)


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_parent(parent_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    parent_service.delete(parent_id, db)
