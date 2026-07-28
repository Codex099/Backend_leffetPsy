from sqlalchemy import Column, String, ForeignKey
from app.db.session import Base


class SeanceEmploye(Base):
    __tablename__ = "seance_employes"

    seance_id = Column(String, ForeignKey("seances.id", ondelete="CASCADE"), primary_key=True)
    employe_id = Column(String, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True)
