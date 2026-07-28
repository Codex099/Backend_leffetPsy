import uuid

from sqlalchemy import Column, String, Text, Date, Integer, ForeignKey
from app.db.session import Base


class EvenementCalendrier(Base):
    __tablename__ = "evenements_calendrier"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    titre = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    notifier_avant_jours = Column(Integer, nullable=True)
    cree_par = Column(String, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
