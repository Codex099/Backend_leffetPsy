import uuid

from sqlalchemy import Column, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class DossierMedical(Base):
    __tablename__ = "dossiers_medicaux"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=False)

    # ── Avant le titre ──────────────────────────────────────────────────────────
    # السوابق المرضية
    antecedents_medicaux = Column(Text, nullable=True)
    # الأدوية المتناولة
    medicaments_pris = Column(Text, nullable=True)

    # ── Historique du cas ───────────────────────────────────────────────────────
    # تاريخ الحالة
    date_cas = Column(Date, nullable=True)
    # الولادة
    naissance = Column(Text, nullable=True)
    # النمو النفسي الحركي
    developpement_psychomoteur = Column(Text, nullable=True)
    # السلوك السمعي
    comportement_auditif = Column(Text, nullable=True)
    # النمو اللغوي
    developpement_langagier = Column(Text, nullable=True)
    # التكيف الاجتماعي
    adaptation_sociale = Column(Text, nullable=True)
    # الاستقلالية
    autonomie = Column(Text, nullable=True)
    # الجانب الصحي
    aspect_sanitaire = Column(Text, nullable=True)
    # مرحلة التمدرس
    stade_scolarisation = Column(Text, nullable=True)

    # ── Méta ────────────────────────────────────────────────────────────────────
    mis_a_jour_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    date_maj = Column(DateTime, default=func.now(), onupdate=func.now())
