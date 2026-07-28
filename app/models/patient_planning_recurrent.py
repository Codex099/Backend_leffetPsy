import uuid
import enum

from sqlalchemy import Column, String, Date, Time, Integer, Enum, ForeignKey
from sqlalchemy.types import JSON
from app.db.session import Base


class ModeGenerationEnum(str, enum.Enum):
    auto = "auto"
    manuel = "manuel"


class PatientPlanningRecurrent(Base):
    __tablename__ = "patient_planning_recurrent"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    jours_semaine = Column(JSON, nullable=False)  # ex: ["jeudi", "dimanche"]
    heure_debut = Column(Time, nullable=True)
    heure_fin = Column(Time, nullable=True)
    date_debut = Column(Date, nullable=False)
    date_fin = Column(Date, nullable=True)
    employe_id = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    mode_generation = Column(Enum(ModeGenerationEnum), nullable=False)
    horizon_jours = Column(Integer, nullable=True)
