from sqlalchemy import Column, String, DateTime
from app.core.database import Base


class RevokedToken(Base):
    """Tokens JWT invalidados al cerrar sesión (se purgan una vez vencidos)."""

    __tablename__ = "revoked_tokens"

    jti = Column(String(36), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
