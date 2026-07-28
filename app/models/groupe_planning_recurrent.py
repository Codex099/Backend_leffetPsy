import uuid
import enum

from sqlalchemy import Column, String, Time, Enum, ForeignKey
from app.db.session import Base


class JourSemaineEnum(str, enum.Enum):
    lundi = "lundi"
    mardi = "mardi"
    mercredi = "mercredi"
    jeudi = "jeudi"
    vendredi = "vendredi"
    samedi = "samedi"
    dimanche = "dimanche"


class GroupePlanningRecurrent(Base):
    __tablename__ = "groupe_planning_recurrent"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    groupe_id = Column(String, ForeignKey("groupes.id", ondelete="CASCADE"), nullable=False)
    jour_semaine = Column(Enum(JourSemaineEnum), nullable=False)
    heure_debut = Column(Time, nullable=True)
    heure_fin = Column(Time, nullable=True)
