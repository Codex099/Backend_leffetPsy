from fastapi import APIRouter, Depends, UploadFile, File
from app.core.security import get_current_employee
from app.services import upload_service

router = APIRouter(prefix="/api/uploads", tags=["Uploads"])


@router.post("", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    _=Depends(get_current_employee),
):
    """
    Upload d'un fichier média.
    Retourne l'URL publique accessible du fichier.
    """
    url = await upload_service.save_file(file)
    return {"url": url}
