import uuid
import enum

from sqlalchemy import Column, String, Enum
from app.db.session import Base


class EtatCivilEnum(str, enum.Enum):
    marie = "marie"
    divorce = "divorce"
    autre = "autre"


class Parent(Base):
    __tablename__ = "parents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    telephone = Column(String, unique=True, nullable=False)  # unique — doublon interdit (US-M17)
    etat_civil = Column(Enum(EtatCivilEnum), nullable=False)
    adresse = Column(String, nullable=True)
