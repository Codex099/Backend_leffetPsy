from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.dossier_medical import DossierMedical
from app.schemas.dossier_medical import DossierMedicalUpdate


def get_by_patient(patient_id: str, db: Session) -> DossierMedical:
    d = db.query(DossierMedical).filter(DossierMedical.patient_id == patient_id).first()
    if not d:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dossier médical introuvable")
    return d


def update(patient_id: str, data: DossierMedicalUpdate, employee_id: str, db: Session) -> DossierMedical:
    dossier = get_by_patient(patient_id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dossier, field, value)
    dossier.mis_a_jour_par = employee_id
    dossier.date_maj = datetime.now(timezone.utc)
    db.commit()
    db.refresh(dossier)
    return dossier
