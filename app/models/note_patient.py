import uuid

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.types import JSON
from app.db.session import Base


class NotePatient(Base):
    __tablename__ = "notes_patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    employe_id = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    seance_id = Column(String, ForeignKey("seances.id", ondelete="SET NULL"), nullable=True)
    seance_groupe_id = Column(String, ForeignKey("seances_groupe.id", ondelete="SET NULL"), nullable=True)
    contenu = Column(Text, nullable=False)
    medias = Column(JSON, nullable=True)
    date_creation = Column(DateTime, default=func.now(), nullable=False)
