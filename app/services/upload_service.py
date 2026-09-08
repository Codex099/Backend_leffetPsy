"""
upload_service.py
Gestion des fichiers uploadés avec stratégie dual :
  - En production (SUPABASE_URL défini) : Supabase Storage (persistant, CDN)
  - En local (pas de SUPABASE_URL)      : disque local dans UPLOAD_DIR
"""
import os
import uuid

from fastapi import UploadFile, HTTPException, status

from app.core.config import settings


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mov", ".avi", ".pdf"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 Mo


async def save_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier uploadé.
    Retourne l'URL publique du fichier.
    - Si SUPABASE_URL est configuré → Supabase Storage (production)
    - Sinon → disque local (développement)
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

    filename = f"{uuid.uuid4()}{ext}"

    # ── Production : Supabase Storage ───────────────────────
    if settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY:
        return await _save_to_supabase(content, filename, ext)

    # ── Développement : disque local ─────────────────────────
    return _save_to_local(content, filename)


async def _save_to_supabase(content: bytes, filename: str, ext: str) -> str:
    """Upload vers Supabase Storage et retourne l'URL publique."""
    try:
        from supabase import create_client

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        bucket = settings.SUPABASE_STORAGE_BUCKET

        # Détermine le content-type
        content_type_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".webp": "image/webp", ".pdf": "application/pdf",
            ".mp4": "video/mp4", ".mov": "video/quicktime",
            ".avi": "video/x-msvideo",
        }
        content_type = content_type_map.get(ext, "application/octet-stream")

        # Upload vers Supabase Storage
        supabase.storage.from_(bucket).upload(
            path=filename,
            file=content,
            file_options={"content-type": content_type},
        )

        # URL publique
        public_url = supabase.storage.from_(bucket).get_public_url(filename)
        return public_url

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur upload Supabase Storage : {str(e)}",
        )


def _save_to_local(content: bytes, filename: str) -> str:
    """Sauvegarde sur disque local (développement uniquement)."""
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    return f"{settings.BASE_URL}/uploads/{filename}"
