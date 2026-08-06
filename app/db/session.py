from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # nécessaire pour SQLite avec FastAPI
    },
)


@event.listens_for(engine, "connect")
def configure_sqlite(dbapi_connection, connection_record):
    """
    Configuration SQLite exécutée à chaque nouvelle connexion :
    - WAL mode : améliore la concurrence lecture/écriture (plusieurs lecteurs + 1 écrivain simultanément)
    - synchronous=NORMAL : bon compromis durabilité/performance (moins de fsync)
    - foreign_keys=ON  : SQLite désactive les FK par défaut — on les réactive
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dépendance FastAPI : fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
