import uuid
from sqlalchemy import Column, String, Text, Integer, Enum, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.etape_plan_therapeutique import StatutEtapeEnum


class SousEtapePlanTherapeutique(Base):
    """
    Sous-étape d'une étape de plan thérapeutique.
    Représente une séance concrète avec la description de ce qui doit être réalisé.
    """
    __tablename__ = "sous_etapes_plan_therapeutique"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    etape_id = Column(
        String,
        ForeignKey("etapes_plan_therapeutique.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=True)  # Ce qu'on doit faire dans chaque séance
    statut = Column(Enum(StatutEtapeEnum), nullable=False, default=StatutEtapeEnum.a_faire)
    ordre = Column(Integer, nullable=False, default=1)
    date_prevue = Column(Date, nullable=True)
    assigne_a = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True)
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)

    assigne_employee = relationship("Employee", foreign_keys=[assigne_a], lazy="joined")

