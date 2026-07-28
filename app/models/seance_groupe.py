import uuid
import enum

from sqlalchemy import Column, String, Date, Time, Enum, ForeignKey
from app.db.session import Base


class StatutSeanceGroupeEnum(str, enum.Enum):
    prevue = "prevue"
    faite = "faite"
    annulee = "annulee"


class SeanceGroupe(Base):
    __tablename__ = "seances_groupe"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    groupe_id = Column(String, ForeignKey("groupes.id", ondelete="CASCADE"), nullable=False)
    employe_id = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    heure_debut = Column(Time, nullable=True)
    heure_fin = Column(Time, nullable=True)
    statut = Column(Enum(StatutSeanceGroupeEnum), nullable=False, default=StatutSeanceGroupeEnum.prevue)
