import uuid
import enum

from sqlalchemy import Column, String, Text, Enum
from app.db.session import Base


class TypePlanningEnum(str, enum.Enum):
    fixe = "fixe"
    ponctuel = "ponctuel"


class Groupe(Base):
    __tablename__ = "groupes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = Column(String, nullable=False)
    type_planning = Column(Enum(TypePlanningEnum), nullable=False)
    description = Column(Text, nullable=True)
