from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.groupe import (
    GroupeCreate, GroupeUpdate, GroupeResponse,
    GroupePlanningRecurrentCreate, GroupePlanningRecurrentResponse,
    AjouterPatientGroupeRequest,
    AjouterEmployeGroupeRequest, AjouterEmployesGroupeRequest, GroupeEmployeResponse,
)
from app.services import groupe_service

router = APIRouter(prefix="/api/groupes", tags=["Groupes"])


@router.get("", response_model=List[GroupeResponse])
def list_groupes(
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """Liste les groupes. Paramètres optionnels : ?search=nom ou description, ?limit=100, ?offset=0."""
    return groupe_service.get_all(db, search=search, limit=limit, offset=offset)


@router.post("", response_model=GroupeResponse, status_code=status.HTTP_201_CREATED)
def create_groupe(data: GroupeCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.create(data, db)


@router.get("/{groupe_id}", response_model=GroupeResponse)
def get_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    """Détail du groupe, membres / planning fixe / responsables imbriqués."""
    return groupe_service.get_detail(groupe_id, db)


@router.put("/{groupe_id}", response_model=GroupeResponse)
@router.patch("/{groupe_id}", response_model=GroupeResponse)
def update_groupe(groupe_id: str, data: GroupeUpdate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.update(groupe_id, data, db)


@router.delete("/{groupe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    groupe_service.delete(groupe_id, db)


@router.get("/{groupe_id}/planning-recurrent", response_model=List[GroupePlanningRecurrentResponse])
def list_planning(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    """Créneaux fixes du groupe — chargés à l'ouverture de l'écran planning récurrent."""
    return groupe_service.get_planning_recurrent(groupe_id, db)


@router.post("/{groupe_id}/planning-recurrent", response_model=GroupePlanningRecurrentResponse, status_code=status.HTTP_201_CREATED)
def set_planning(groupe_id: str, data: GroupePlanningRecurrentCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.set_planning_recurrent(groupe_id, data, db)


# ─── Routes patients membres du groupe ────────────────────────────────────────

@router.get("/{groupe_id}/patients")
def list_patients_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    """Liste les patients membres du groupe (nom, prénom, photo, statut)."""
    return groupe_service.get_patients(groupe_id, db)


@router.post("/{groupe_id}/patients", status_code=status.HTTP_201_CREATED)
def add_patient(groupe_id: str, data: AjouterPatientGroupeRequest, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return groupe_service.add_patient(groupe_id, data.patient_id, db)


@router.delete("/{groupe_id}/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_patient_groupe(
    groupe_id: str,
    patient_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """Retire un patient du groupe (l'accès employé au patient n'est pas révoqué)."""
    groupe_service.remove_patient(groupe_id, patient_id, db)


# ─── Routes employés responsables du groupe (US-M20 / US-M24) ────────────────

@router.get("/{groupe_id}/employes", response_model=List[GroupeEmployeResponse])
def list_employes_groupe(groupe_id: str, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    """Liste les employés responsables associés au groupe."""
    return groupe_service.get_employes(groupe_id, db)


@router.post("/{groupe_id}/employes", response_model=GroupeEmployeResponse, status_code=status.HTTP_201_CREATED)
def add_employe_groupe(
    groupe_id: str,
    data: AjouterEmployeGroupeRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """
    Associe un employé au groupe en tant que responsable.
    Propage automatiquement l'accès à tous les patients membres dans employee_patient_access.
    """
    return groupe_service.add_employe(groupe_id, data.employe_id, db)


@router.post("/{groupe_id}/employes/bulk", status_code=status.HTTP_201_CREATED)
def add_employes_groupe_bulk(
    groupe_id: str,
    data: AjouterEmployesGroupeRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """Associe plusieurs employés au groupe en une seule opération (idempotent)."""
    return groupe_service.add_employes(groupe_id, data.employe_ids, db)


@router.delete("/{groupe_id}/employes/{employe_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_employe_groupe(
    groupe_id: str,
    employe_id: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_employee),
):
    """Retire un employé de la liste des responsables du groupe."""
    groupe_service.remove_employe(groupe_id, employe_id, db)
