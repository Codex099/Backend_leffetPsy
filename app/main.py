import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import engine, Base
import app.models  # Charge tous les modèles SQLAlchemy

from app.services.planning_service import run_auto_generation
from app.routes import (
    auth,
    parents,
    patients,
    dossiers_medicaux,
    employees,
    groupes,
    seances,
    seances_groupe,
    taches,
    calendrier,
    plans_therapeutiques,
    notes_patients,
    uploads,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("psycare")

# Scheduler APScheduler pour la génération automatique des créneaux récurrents
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Création des tables DB au démarrage
    logger.info("Création des tables de base de données si absentes...")
    Base.metadata.create_all(bind=engine)

    # 2. Démarrage de la tâche de génération automatique de créneaux
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    scheduler.add_job(run_auto_generation, "interval", hours=24, id="auto_planning_job")
    scheduler.start()
    logger.info("Scheduler APScheduler démarré (auto-generation quotidienne)")

    yield

    # Arrêt propre du scheduler
    scheduler.shutdown()
    logger.info("Scheduler APScheduler arrêté")


app = FastAPI(
    title="PsyCare API",
    description="API REST Backend pour la clinique de psychologie PsyCare",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S'assurer que le dossier d'upload existe avant le montage StaticFiles
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Montage du dossier d'uploads pour servir les fichiers statiques
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# Enregistrement des routers
app.include_router(auth.router)
app.include_router(parents.router)
app.include_router(patients.router)
app.include_router(dossiers_medicaux.router)
app.include_router(employees.router)
app.include_router(groupes.router)
app.include_router(seances.router)
app.include_router(seances_groupe.router)
app.include_router(taches.router)
app.include_router(calendrier.router)
app.include_router(plans_therapeutiques.router)
app.include_router(notes_patients.router)
app.include_router(uploads.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "PsyCare Backend"}
