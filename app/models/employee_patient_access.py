from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class EmployeePatientAccess(Base):
    __tablename__ = "employee_patient_access"

    # Les deux colonnes sont indexées car elles sont utilisées ensemble dans presque toutes les requêtes
    # de contrôle d'accès (check_patient_access / get_accessible_patient_ids)
    employee_id = Column(String, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True, index=True)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True, index=True)
