import uuid

from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class PlanTherapeutique(Base):
    __tablename__ = "plans_therapeutiques"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
