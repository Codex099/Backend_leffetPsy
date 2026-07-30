import uuid

from sqlalchemy import Column, String, Date, Integer, Boolean, DateTime
from app.db.session import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    date_naissance = Column(Date, nullable=True)
    photo = Column(String, nullable=True)
    nombre_freres_soeurs = Column(Integer, nullable=True)
    ordre_naissance = Column(Integer, nullable=True)

    # Gestion du statut actif / inactif
    est_actif = Column(Boolean, nullable=False, default=True)
    date_desactivation = Column(DateTime, nullable=True)  # rempli auto à la désactivation
    date_reactivation = Column(DateTime, nullable=True)   # rempli auto à la réactivation
