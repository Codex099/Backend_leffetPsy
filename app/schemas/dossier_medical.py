from typing import Optional
from datetime import datetime, date
from pydantic import BaseModel


class DossierMedicalBase(BaseModel):
    # ── Avant le titre ──────────────────────────────────────────────────────────
    antecedents_medicaux: Optional[str] = None       # السوابق المرضية
    medicaments_pris: Optional[str] = None           # الأدوية المتناولة

    # ── Historique du cas ───────────────────────────────────────────────────────
    date_cas: Optional[date] = None                  # تاريخ الحالة
    naissance: Optional[str] = None                  # الولادة
    developpement_psychomoteur: Optional[str] = None # النمو النفسي الحركي
    comportement_auditif: Optional[str] = None       # السلوك السمعي
    developpement_langagier: Optional[str] = None    # النمو اللغوي
    adaptation_sociale: Optional[str] = None         # التكيف الاجتماعي
    autonomie: Optional[str] = None                  # الاستقلالية
    aspect_sanitaire: Optional[str] = None           # الجانب الصحي
    stade_scolarisation: Optional[str] = None        # مرحلة التمدرس


class DossierMedicalUpdate(DossierMedicalBase):
    pass


class DossierMedicalResponse(DossierMedicalBase):
    id: str
    patient_id: str
    mis_a_jour_par: Optional[str] = None
    date_maj: Optional[datetime] = None

    model_config = {"from_attributes": True}
