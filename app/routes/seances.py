from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.seance import (
    SeanceCreate, SeanceUpdate, SeanceResponse,
    PatientPlanningRecurrentCreate, PatientPlanningRecurrentResponse,
    GenererCreneauxRequest,
)
from app.services import seance_service
from app.services import planning_service
from app.services.access_control_service import check_patient_access

router = APIRouter(tags=["Séances"])


# ── Séances individuelles ──────────────────────────────────────────────────────

@router.get("/api/seances", response_model=List[SeanceResponse])
def list_seances(db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return seance_service.get_all(employee, db)


@router.post("/api/seances", response_model=SeanceResponse, status_code=status.HTTP_201_CREATED)
def create_seance(data: SeanceCreate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(data.patient_id, employee, db)
    return seance_service.create(data, db)


@router.get("/api/seances/{seance_id}", response_model=SeanceResponse)
def get_seance(seance_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    seance = seance_service.get_by_id(seance_id, db)
    check_patient_access(seance.patient_id, employee, db)
    return seance


@router.put("/api/seances/{seance_id}", response_model=SeanceResponse)
def update_seance(seance_id: str, data: SeanceUpdate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    seance = seance_service.get_by_id(seance_id, db)
    check_patient_access(seance.patient_id, employee, db)
    return seance_service.update(seance_id, data, db)


@router.delete("/api/seances/{seance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_seance(seance_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    seance = seance_service.get_by_id(seance_id, db)
    check_patient_access(seance.patient_id, employee, db)
    seance_service.delete(seance_id, db)


# ── Planning récurrent patient ─────────────────────────────────────────────────

@router.get("/api/patients/{patient_id}/planning-recurrent", response_model=PatientPlanningRecurrentResponse)
def get_planning(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    planning = seance_service.get_planning_recurrent(patient_id, db)
    if not planning:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Aucun planning récurrent configuré")
    return planning


@router.post("/api/patients/{patient_id}/planning-recurrent", response_model=PatientPlanningRecurrentResponse, status_code=status.HTTP_201_CREATED)
def set_planning(patient_id: str, data: PatientPlanningRecurrentCreate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return seance_service.set_planning_recurrent(patient_id, data, db)


@router.post("/api/patients/{patient_id}/planning-recurrent/generer")
def generer_creneaux(patient_id: str, data: GenererCreneauxRequest, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    planning = seance_service.get_planning_recurrent(patient_id, db)
    if not planning:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Aucun planning récurrent configuré")
    count = planning_service.generer_creneaux_manuel(planning, data.date_debut, data.date_fin, db)
    return {"message": f"{count} créneaux générés"}
