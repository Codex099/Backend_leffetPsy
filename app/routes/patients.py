from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee, require_roles
from app.models.patient import SexeEnum
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, AssocierParentRequest, ChangerStatutRequest
from app.schemas.patient_statut_historique import PatientStatutHistoriqueResponse, NotesDegradationUpdate
from app.services import patient_service
from app.services import patient_statut_service
from app.services.access_control_service import check_patient_access

router = APIRouter(prefix="/api/patients", tags=["Patients"])

psychologue_or_admin = require_roles("psychologue", "admin")


@router.get("", response_model=List[PatientResponse])
def list_patients(
    actif: Optional[bool] = None,
    sexe: Optional[SexeEnum] = None,
    age_min: Optional[int] = None,
    age_max: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    """Liste les patients. Paramètres optionnels : ?actif=true/false, ?sexe=masculin|feminin, ?age_min=5, ?age_max=12, ?limit=100, ?offset=0."""
    return patient_service.get_all(
        employee, db, actif=actif, sexe=sexe, age_min=age_min, age_max=age_max, limit=limit, offset=offset
    )


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(data: PatientCreate, db: Session = Depends(get_db), _=Depends(get_current_employee)):
    return patient_service.create(data, db)


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    return check_patient_access(patient_id, employee, db)


@router.put("/{patient_id}", response_model=PatientResponse)
@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, data: PatientUpdate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return patient_service.update(patient_id, data, db)


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    patient_service.delete(patient_id, db)


@router.post("/{patient_id}/parents", status_code=status.HTTP_201_CREATED)
def associer_parent(patient_id: str, data: AssocierParentRequest, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return patient_service.associer_parent(patient_id, data, db)


@router.get("/{patient_id}/parents")
def get_patient_parents(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return patient_service.get_parents(patient_id, db)



# ─── Statut actif / inactif ───────────────────────────────────────────────────

@router.put("/{patient_id}/statut", response_model=PatientResponse)
@router.patch("/{patient_id}/statut", response_model=PatientResponse)
def changer_statut_patient(
    patient_id: str,
    data: ChangerStatutRequest,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    """
    Active ou désactive un patient.

    - `est_actif=false` → désactivation, enregistrement dans l'historique.
    - `est_actif=true`  → réactivation, enregistrement dans l'historique.
    - `note_degradation` (optionnel) : note manuelle du psychologue lors d'une réactivation.
    """
    check_patient_access(patient_id, employee, db)
    return patient_statut_service.changer_statut(patient_id, data, employee.id, db)


@router.get("/{patient_id}/statut-historique", response_model=List[PatientStatutHistoriqueResponse])
def get_statut_historique(
    patient_id: str,
    db: Session = Depends(get_db),
    employee=Depends(get_current_employee),
):
    """Retourne l'historique complet des changements de statut du patient."""
    check_patient_access(patient_id, employee, db)
    return patient_statut_service.get_historique(patient_id, db)


@router.put("/{patient_id}/statut-historique/{historique_id}", response_model=PatientStatutHistoriqueResponse)
@router.patch("/{patient_id}/statut-historique/{historique_id}", response_model=PatientStatutHistoriqueResponse)
def update_note_degradation(
    patient_id: str,
    historique_id: str,
    data: NotesDegradationUpdate,
    db: Session = Depends(get_db),
    employee=Depends(psychologue_or_admin),
):
    """Ajoute ou modifie la note de dégradation sur une entrée d'historique."""
    check_patient_access(patient_id, employee, db)
    return patient_statut_service.update_note_degradation(patient_id, historique_id, data.note_degradation, db)

