from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import require_admin
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse, AssignPatientRequest, GlobalVisibilityRequest
from app.services import employee_service

router = APIRouter(prefix="/api/employees", tags=["Employees"])


@router.get("", response_model=List[EmployeeResponse])
def list_employees(
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """Liste les employés. Paramètres optionnels : ?search=nom, prénom, téléphone ou username, ?limit=100, ?offset=0."""
    return employee_service.get_all(db, search=search, limit=limit, offset=offset)


@router.post("", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.create(data, db)


@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.get_by_id(employee_id, db)


@router.put("/{employee_id}", response_model=EmployeeResponse)
@router.patch("/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: str, data: EmployeeUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.update(employee_id, data, db)


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(employee_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    employee_service.delete(employee_id, db)


@router.post("/{employee_id}/patients", status_code=status.HTTP_201_CREATED)
def assign_patient(employee_id: str, data: AssignPatientRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    return employee_service.assign_patient(employee_id, data, db)


@router.get("/{employee_id}/visibilite-patients")
def get_visibility_details(employee_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Retourne la liste des patients visibles et invisibles pour un employé donné (Admin uniquement)."""
    return employee_service.get_visibility_details(employee_id, db)


@router.post("/visibilite-globale")
def apply_global_visibility(data: GlobalVisibilityRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Accorde ou révoque la visibilité de tous les patients pour toute l'équipe ou une sélection d'employés (Admin uniquement)."""
    return employee_service.apply_global_visibility(data, db)
