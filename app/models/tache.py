import uuid
import enum

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class StatutTacheEnum(str, enum.Enum):
    a_faire = "a_faire"
    en_cours = "en_cours"
    fait = "fait"


class PrioriteTacheEnum(str, enum.Enum):
    basse = "basse"
    normale = "normale"
    haute = "haute"


class Tache(Base):
    __tablename__ = "taches"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assigne_a = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)  # indexé
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="SET NULL"), nullable=True)
    etape_plan_id = Column(String, ForeignKey("etapes_plan_therapeutique.id", ondelete="SET NULL"), nullable=True)
    statut = Column(Enum(StatutTacheEnum), nullable=False, default=StatutTacheEnum.a_faire, index=True)  # indexé
    priorite = Column(Enum(PrioriteTacheEnum), nullable=False, default=PrioriteTacheEnum.normale)
    date_echeance = Column(DateTime, nullable=True)
