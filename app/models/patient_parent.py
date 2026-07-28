import enum

from sqlalchemy import Column, String, Enum, ForeignKey
from app.db.session import Base


class RoleParentEnum(str, enum.Enum):
    pere = "pere"
    mere = "mere"
    tuteur = "tuteur"
    autre = "autre"


class PatientParent(Base):
    __tablename__ = "patient_parents"

    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    parent_id = Column(String, ForeignKey("parents.id", ondelete="CASCADE"), primary_key=True)
    role = Column(Enum(RoleParentEnum), nullable=False)
