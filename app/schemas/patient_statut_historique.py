from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.models.patient_statut_historique import StatutPatientEnum


class PatientStatutHistoriqueResponse(BaseModel):
    """Réponse complète d'une entrée d'historique de statut."""
    id: str
    patient_id: str
    statut: StatutPatientEnum
    date_changement: datetime
    change_par: Optional[str] = None
    note_degradation: Optional[str] = None

    model_config = {"from_attributes": True}


class NotesDegradationUpdate(BaseModel):
    """Payload pour ajouter / modifier la note de dégradation sur une entrée d'historique."""
    note_degradation: str
