import uuid
import enum

from sqlalchemy import Column, String, Date, Enum, ForeignKey
from app.db.session import Base


class StatutPlanEnum(str, enum.Enum):
    actif = "actif"
    archive = "archive"
    suspendu = "suspendu"


class PlanTherapeutique(Base):
    """
    Plan thérapeutique d'un patient.

    Un patient peut avoir plusieurs plans simultanément ou successifs.
    La contrainte unique sur patient_id a été supprimée pour supporter ce cas.
    """

    __tablename__ = "plans_therapeutiques"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    # Note : pas de contrainte unique — multi-plans autorisés
    patient_id = Column(
        String,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titre = Column(String, nullable=False)  # ex: "Plan orthophonie", "Plan comportemental"
    statut = Column(Enum(StatutPlanEnum), nullable=False, default=StatutPlanEnum.actif)
    date_debut = Column(Date, nullable=True)
    date_fin = Column(Date, nullable=True)
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
