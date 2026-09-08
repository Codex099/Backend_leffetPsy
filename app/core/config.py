from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./psycare.db"
    UPLOAD_DIR: str = "uploads"
    BASE_URL: str = "http://localhost:8000"
    CRON_SECRET: str = "secret-local"

    # Cloudinary Storage — pour les fichiers uploadés (fallback backend)
    # Trouver dans : Cloudinary → Dashboard → Account Details
    CLOUDINARY_CLOUD_NAME: Optional[str] = None   # ex: dupnlcne9
    CLOUDINARY_API_KEY: Optional[str] = None       # ex: 733821433592611
    CLOUDINARY_API_SECRET: Optional[str] = None    # depuis le dashboard
    CLOUDINARY_UPLOAD_PRESET: str = "psycare_uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
