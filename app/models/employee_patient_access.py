from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class EmployeePatientAccess(Base):
    __tablename__ = "employee_patient_access"

    employee_id = Column(String, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True)
