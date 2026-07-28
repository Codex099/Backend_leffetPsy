import uuid
import enum

from sqlalchemy import Column, String, Enum
from app.db.session import Base


class RoleEmployeEnum(str, enum.Enum):
    admin = "admin"
    psychologue = "psychologue"
    educatrice = "educatrice"


class Employee(Base):
    __tablename__ = "employees"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    telephone = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEmployeEnum), nullable=False)
