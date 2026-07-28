from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class PatientGroupe(Base):
    __tablename__ = "patients_groupes"

    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
    groupe_id = Column(String, ForeignKey("groupes.id", ondelete="CASCADE"), primary_key=True)
