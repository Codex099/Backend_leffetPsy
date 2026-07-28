import enum

from sqlalchemy import Column, String, Text, Enum, ForeignKey
from sqlalchemy.types import JSON
from app.db.session import Base


class StatutPresenceGroupeEnum(str, enum.Enum):
    present = "present"
    absent = "absent"
    excuse = "excuse"


class SeanceGroupeParticipant(Base):
    __tablename__ = "seance_groupe_participants"

    seance_groupe_id = Column(String, ForeignKey("seances_groupe.id", ondelete="CASCADE"), primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    statut_presence = Column(Enum(StatutPresenceGroupeEnum), nullable=True)
    description_etat = Column(Text, nullable=True)
    reponses_questionnaire = Column(JSON, nullable=True)
    redige_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    medias = Column(JSON, nullable=True)
