from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class GroupeEmploye(Base):
    """
    Table de jointure N-N entre groupes et employees.
    Décision produit (US-M20 / US-M24) : structure à plat, sans champ de rôle ou de priorité —
    tous les employés associés à un groupe ont le même statut.
    """
    __tablename__ = "groupe_employes"

    groupe_id = Column(String, ForeignKey("groupes.id", ondelete="CASCADE"), primary_key=True)
    employe_id = Column(String, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
