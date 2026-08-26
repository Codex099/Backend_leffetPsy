"""
Schémas Pydantic pour le connecteur MCP Agent IA.

Couvre les 6 user stories :
  US1 — Tokens API personnels (génération, révocation)
  US2 — Recherche patient + dossier médical
  US3 — Historique séances
  US4 — Liste plans thérapeutiques + statut étapes
  US5 — Création plan avec étapes
  US6 — Modification plan / étape
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel

from app.schemas.plan_therapeutique import EtapeCreate, EtapeUpdate


# ─── US1 : Tokens MCP ────────────────────────────────────────────────────────

class McpTokenCreate(BaseModel):
    """Payload pour générer un nouveau token MCP."""
    nom: str  # ex: "Claude Desktop", "Mon agent local"


class McpTokenResponse(BaseModel):
    """Réponse après génération — le `token` en clair n'est affiché qu'une fois."""
    id: str
    nom: str
    created_at: datetime
    token: Optional[str] = None  # présent uniquement à la création

    model_config = {"from_attributes": True}


class McpTokenListItem(BaseModel):
    """Item de la liste des tokens (sans le token en clair)."""
    id: str
    nom: str
    created_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─── US5 : Création plan avec étapes ─────────────────────────────────────────

class McpPlanCreate(BaseModel):
    """
    Payload pour créer un plan thérapeutique complet avec ses étapes en une seule requête.
    Utilisé par l'agent IA après validation explicite du psychologue.
    """
    titre: str
    statut: str = "actif"
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    etapes: List[EtapeCreate] = []


# ─── US6 : Modification plan / étape ─────────────────────────────────────────

class McpPlanUpdate(BaseModel):
    """Payload PATCH pour modifier un plan thérapeutique."""
    titre: Optional[str] = None
    statut: Optional[str] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None


class McpEtapeUpdate(BaseModel):
    """Payload PATCH pour modifier une étape d'un plan thérapeutique."""
    titre: Optional[str] = None
    description: Optional[str] = None
    statut: Optional[str] = None
    ordre: Optional[int] = None
