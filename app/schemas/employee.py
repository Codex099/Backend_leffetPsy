from typing import Optional
from pydantic import BaseModel
from app.models.employee import RoleEmployeEnum


class EmployeeBase(BaseModel):
    nom: str
    prenom: str
    telephone: str
    username: str
    role: RoleEmployeEnum


class EmployeeCreate(EmployeeBase):
    password: str


class EmployeeUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    telephone: Optional[str] = None
    username: Optional[str] = None
    role: Optional[RoleEmployeEnum] = None
    password: Optional[str] = None


class EmployeeResponse(EmployeeBase):
    id: str

    model_config = {"from_attributes": True}


class AssignPatientRequest(BaseModel):
    patient_id: str
