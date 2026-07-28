from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.dossier_medical import DossierMedicalUpdate, DossierMedicalResponse
from app.services import dossier_medical_service
from app.services.access_control_service import check_patient_access

router = APIRouter(prefix="/api/patients", tags=["Dossiers Médicaux"])


@router.get("/{patient_id}/dossier-medical", response_model=DossierMedicalResponse)
def get_dossier(patient_id: str, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return dossier_medical_service.get_by_patient(patient_id, db)


@router.put("/{patient_id}/dossier-medical", response_model=DossierMedicalResponse)
def update_dossier(patient_id: str, data: DossierMedicalUpdate, db: Session = Depends(get_db), employee=Depends(get_current_employee)):
    check_patient_access(patient_id, employee, db)
    return dossier_medical_service.update(patient_id, data, employee.id, db)
