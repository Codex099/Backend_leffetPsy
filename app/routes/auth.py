from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_employee
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.employee import EmployeeResponse
from app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    """Login username + password → access token JWT (compatible JSON mobile et formulaire Swagger)."""
    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
    else:
        try:
            body = await request.json()
            if isinstance(body, dict):
                username = body.get("username")
                password = body.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(
            status_code=422,
            detail="Username et mot de passe requis",
        )

    token = auth_service.login(username, password, db)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=EmployeeResponse)
def me(employee=Depends(get_current_employee), db: Session = Depends(get_db)):
    """Retourne les infos de l'employé connecté avec ses patients assignés."""
    from app.services.employee_service import _enrich_employee
    return _enrich_employee(employee, db)

