import uuid
import enum

from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.session import Base


class McpToken(Base):
    """
    Token API personnel pour l'authentification du connecteur MCP.

    Un psychologue génère son token via POST /api/auth/mcp-token.
    Le raw token est affiché une seule fois (non stocké en clair).
    token_hash est un SHA-256 du token brut.
    """

    __tablename__ = "mcp_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = Column(
        String,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash = Column(String, unique=True, nullable=False, index=True)
    nom = Column(Text, nullable=False)  # label lisible ex: "Claude Desktop"
    created_at = Column(DateTime, default=func.now(), nullable=False)
    revoked_at = Column(DateTime, nullable=True)  # NULL = actif
