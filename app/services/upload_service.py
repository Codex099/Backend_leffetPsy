"""
upload_service.py
Gestion des fichiers uploades avec strategie dual :
  - En production (CLOUDINARY_CLOUD_NAME defini) : Cloudinary (CDN, illimite)
  - En local (pas de CLOUDINARY_CLOUD_NAME)      : disque local dans UPLOAD_DIR
"""
import os
import uuid

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".pdf"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Mo


async def save_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier uploade.
    Retourne l'URL publique du fichier.
    - Si CLOUDINARY_CLOUD_NAME est configure -> Cloudinary (production)
    - Sinon -> disque local (developpement)
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extension non autorisee. Extensions acceptees : {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Fichier trop volumineux (max 15 Mo)",
        )

    filename = f"{uuid.uuid4()}{ext}"

    # -- Production : Cloudinary -----------------------------------
    if settings.CLOUDINARY_CLOUD_NAME and settings.CLOUDINARY_API_KEY:
        return await _save_to_cloudinary(content, filename, ext)

    # -- Developpement : disque local ------------------------------
    return _save_to_local(content, filename)


async def _save_to_cloudinary(content: bytes, filename: str, ext: str) -> str:
    """Upload vers Cloudinary et retourne l'URL publique secure."""
    try:
        import cloudinary
        import cloudinary.uploader

        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
        )

        # Determine resource_type selon le fichier
        resource_type = "video" if ext in {".mp4", ".mov", ".avi"} else "auto"

        result = cloudinary.uploader.upload(
            content,
            public_id=filename.rsplit(".", 1)[0],  # sans extension
            resource_type=resource_type,
            overwrite=False,
        )

        return result.get("secure_url", "")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload Cloudinary : {str(e)}",
        )


def _save_to_local(content: bytes, filename: str) -> str:
    """Sauvegarde sur disque local (developpement uniquement)."""
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    return f"{settings.BASE_URL}/uploads/{filename}"
