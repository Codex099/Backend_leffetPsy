from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.groupe import (
    GroupeCreate, GroupeUpdate, GroupeResponse,
    GroupePlanningRecurrentCreate, GroupePlanningRecurrentResponse,
    AjouterPatientGroupeRequest,
)
from app.services import groupe_service

router = APIRouter(prefix="/api/groupes", tags=["Groupes"])


@router.get("", response_model=List[GroupeResponse])
def list_groupes(db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.get_all(db)


@router.post("", response_model=GroupeResponse, status_code=status.HTTP_201_CREATED)
def create_groupe(data: GroupeCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.create(data, db)


@router.get("/{groupe_id}", response_model=GroupeResponse)
def get_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.get_by_id(groupe_id, db)


@router.put("/{groupe_id}", response_model=GroupeResponse)
def update_groupe(groupe_id: str, data: GroupeUpdate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.update(groupe_id, data, db)


@router.delete("/{groupe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    groupe_service.delete(groupe_id, db)


@router.post("/{groupe_id}/planning-recurrent", response_model=GroupePlanningRecurrentResponse, status_code=status.HTTP_201_CREATED)
def set_planning(groupe_id: str, data: GroupePlanningRecurrentCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.set_planning_recurrent(groupe_id, data, db)


@router.post("/{groupe_id}/patients", status_code=status.HTTP_201_CREATED)
def add_patient(groupe_id: str, data: AjouterPatientGroupeRequest, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.add_patient(groupe_id, data.patient_id, db)
