import uuid
import enum

from sqlalchemy import Column, String, Date, Time, Text, Enum, ForeignKey
from sqlalchemy.types import JSON
from app.db.session import Base


class StatutSeanceEnum(str, enum.Enum):
    prevue = "prevue"
    faite = "faite"
    annulee = "annulee"
    retardee = "retardee"


class StatutPresenceEnum(str, enum.Enum):
    present = "present"
    absent = "absent"
    excuse = "excuse"


class Seance(Base):
    __tablename__ = "seances"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)  # indexé
    date = Column(Date, nullable=False, index=True)  # indexé — tri et filtre fréquents
    heure_debut = Column(Time, nullable=True)
    heure_fin = Column(Time, nullable=True)
    statut = Column(Enum(StatutSeanceEnum), nullable=False, default=StatutSeanceEnum.prevue)
    motif_statut = Column(Text, nullable=True)
    statut_presence = Column(Enum(StatutPresenceEnum), nullable=True)
    description_etat = Column(Text, nullable=True)
    reponses_questionnaire = Column(JSON, nullable=True)
    medias = Column(JSON, nullable=True)
