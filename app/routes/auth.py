from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.employee import EmployeeResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Login username + password → access token JWT."""
    token = auth_service.login(data.username, data.password, db)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=EmployeeResponse)
def me(employee=Depends(get_current_employee)):
    """Retourne les infos de l'employé connecté."""
    return employee
