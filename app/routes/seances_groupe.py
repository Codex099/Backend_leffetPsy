from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.seance_groupe import SeanceGroupeCreate, SeanceGroupeUpdate, SeanceGroupeResponse, ParticipantUpdate, ParticipantResponse
from app.services import seance_groupe_service

router = APIRouter(prefix="/api/seances-groupe", tags=["Séances de Groupe"])


@router.get("", response_model=List[SeanceGroupeResponse])
def list_seances_groupe(limit: int = 100, offset: int = 0, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return seance_groupe_service.get_all(db, limit=limit, offset=offset)


@router.post("", response_model=SeanceGroupeResponse, status_code=status.HTTP_201_CREATED)
def create_seance_groupe(data: SeanceGroupeCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return seance_groupe_service.create(data, db)


@router.get("/{seance_id}", response_model=SeanceGroupeResponse)
def get_seance_groupe(seance_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return seance_groupe_service.get_by_id(seance_id, db)


@router.put("/{seance_id}", response_model=SeanceGroupeResponse)
@router.patch("/{seance_id}", response_model=SeanceGroupeResponse)
def update_seance_groupe(seance_id: str, data: SeanceGroupeUpdate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return seance_groupe_service.update(seance_id, data, db)


@router.delete("/{seance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seance_groupe(seance_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    seance_groupe_service.delete(seance_id, db)


@router.put("/{seance_id}/participants/{patient_id}", response_model=ParticipantResponse)
@router.patch("/{seance_id}/participants/{patient_id}", response_model=ParticipantResponse)
def update_participant(seance_id: str, patient_id: str, data: ParticipantUpdate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return seance_groupe_service.update_participant(seance_id, patient_id, data, employee.id, db)
