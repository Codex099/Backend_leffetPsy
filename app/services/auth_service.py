from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.core.security import verify_password, create_access_token


def login(username: str, password: str, db: Session) -> str:
    """Vérifie les credentials et retourne un access token JWT."""
    employee = db.query(Employee).filter(Employee.username == username).first()
    if not employee or not verify_password(password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
        )
    token = create_access_token({"sub": employee.id, "role": employee.role})
    return token
