from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.tache import TacheCreate, TacheUpdate, TacheResponse
from app.services import tache_service

router = APIRouter(prefix="/api/taches", tags=["Tâches"])


@router.get("", response_model=List[TacheResponse])
def list_taches(limit: int = 100, offset: int = 0, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return tache_service.get_all(employee, db, limit=limit, offset=offset)


@router.post("", response_model=TacheResponse, status_code=status.HTTP_201_CREATED)
def create_tache(data: TacheCreate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return tache_service.create(data, employee.id, db)


@router.get("/{tache_id}", response_model=TacheResponse)
def get_tache(tache_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return tache_service.get_by_id(tache_id, db)


@router.put("/{tache_id}", response_model=TacheResponse)
@router.patch("/{tache_id}", response_model=TacheResponse)
def update_tache(tache_id: str, data: TacheUpdate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return tache_service.update(tache_id, data, db)


@router.delete("/{tache_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tache(tache_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    tache_service.delete(tache_id, db)
