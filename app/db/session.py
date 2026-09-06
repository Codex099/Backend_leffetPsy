from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# PostgreSQL : pas besoin de check_same_thread (spécifique à SQLite)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # vérifie la connexion avant utilisation (robustesse pooler)
    pool_size=5,              # connexions persistantes dans le pool
    max_overflow=10,          # connexions supplémentaires si pool saturé
    pool_recycle=300,         # recycle les connexions après 5 min (évite les timeouts Supabase)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI : fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
