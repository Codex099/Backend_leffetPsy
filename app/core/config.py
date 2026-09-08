from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./psycare.db"
    UPLOAD_DIR: str = "uploads"
    BASE_URL: str = "http://localhost:8000"
    CRON_SECRET: str = "secret-local"

    # Supabase Storage — pour les fichiers uploadés en production
    # Trouver dans : Supabase → Settings → API
    SUPABASE_URL: Optional[str] = None         # ex: https://rvwpwbwrilvojorhhhde.supabase.co
    SUPABASE_ANON_KEY: Optional[str] = None    # clé "anon public"
    SUPABASE_STORAGE_BUCKET: str = "psycare-uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
