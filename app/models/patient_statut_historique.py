import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from app.db.session import Base


class StatutPatientEnum(str, enum.Enum):
    actif = "actif"
    inactif = "inactif"


class PatientStatutHistorique(Base):
    """
    Trace chaque changement de statut (actif ↔ inactif) pour un patient.

    Le champ note_degradation est saisi manuellement par le psychologue
    lors d'une réactivation pour signaler que l'état du patient s'est
    dégradé pendant la période d'inactivité. Il reste nullable.
    """

    __tablename__ = "patient_statut_historique"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(
        String,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statut = Column(Enum(StatutPatientEnum), nullable=False)
    date_changement = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    change_par = Column(
        String,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Note manuelle du psychologue si l'état s'est dégradé au retour (réactivation)
    note_degradation = Column(Text, nullable=True)
