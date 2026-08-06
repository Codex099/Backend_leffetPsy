import os
import uuid

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".pdf"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Mo — limite raisonnable pour préserver le disque de la VM Oracle Cloud


async def save_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier uploadé dans le dossier UPLOAD_DIR.
    Retourne l'URL publique du fichier.
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extension non autorisée. Extensions acceptées : {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 15 Mo)",
        )

    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    return f"{settings.BASE_URL}/uploads/{filename}"
