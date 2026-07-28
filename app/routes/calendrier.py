from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.calendrier import EvenementCalendrierCreate, EvenementCalendrierUpdate, EvenementCalendrierResponse
from app.services import calendrier_service

router = APIRouter(prefix="/api/calendrier", tags=["Calendrier"])


@router.get("", response_model=List[EvenementCalendrierResponse])
def list_evenements(db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return calendrier_service.get_all(db)


@router.post("", response_model=EvenementCalendrierResponse, status_code=status.HTTP_201_CREATED)
def create_evenement(data: EvenementCalendrierCreate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return calendrier_service.create(data, employee.id, db)


@router.get("/{event_id}", response_model=EvenementCalendrierResponse)
def get_evenement(event_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return calendrier_service.get_by_id(event_id, db)


@router.put("/{event_id}", response_model=EvenementCalendrierResponse)
def update_evenement(event_id: str, data: EvenementCalendrierUpdate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return calendrier_service.update(event_id, data, db)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evenement(event_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    calendrier_service.delete(event_id, db)
