from fastapi import APIRouter, Depends, HTTPException, status, Header
import logging
from app.services.planning_service import run_auto_generation
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cron", tags=["cron"])

def verify_cron_secret(authorization: str = Header(None)):
    """Vérifie que la requête vient bien de Vercel Cron via le token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")
    
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Authorization header format")
    
    token = parts[1]
    if token != settings.CRON_SECRET:
        logger.warning("Tentative d'accès non autorisée au Cron")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Cron Secret")

@router.get("/run-planning", dependencies=[Depends(verify_cron_secret)])
def trigger_auto_generation():
    """
    Route appelée par Vercel Cron tous les jours pour générer les plannings.
    """
    logger.info("Déclenchement manuel/Cron de la génération automatique des plannings...")
    run_auto_generation()
    return {"status": "success", "message": "Génération automatique exécutée"}
