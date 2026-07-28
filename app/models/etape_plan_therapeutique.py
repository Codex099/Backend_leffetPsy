import uuid
import enum

from sqlalchemy import Column, String, Text, Integer, Enum, ForeignKey
from app.db.session import Base


class StatutEtapeEnum(str, enum.Enum):
    a_faire = "a_faire"
    en_cours = "en_cours"
    fait = "fait"


class EtapePlanTherapeutique(Base):
    __tablename__ = "etapes_plan_therapeutique"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String, ForeignKey("plans_therapeutiques.id", ondelete="CASCADE"), nullable=False)
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    statut = Column(Enum(StatutEtapeEnum), nullable=False, default=StatutEtapeEnum.a_faire)
    ordre = Column(Integer, nullable=False)
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
