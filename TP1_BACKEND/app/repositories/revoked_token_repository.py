from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.revoked_token import RevokedToken


class RevokedTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def is_revoked(self, jti: str) -> bool:
        return self.db.query(RevokedToken.jti).filter(RevokedToken.jti == jti).first() is not None

    def revoke(self, jti: str, expires_at: datetime) -> None:
        """Registra el token como revocado y purga los que ya vencieron por sí solos."""
        self.db.query(RevokedToken).filter(
            RevokedToken.expires_at < datetime.now(timezone.utc)
        ).delete()
        if not self.is_revoked(jti):
            self.db.add(RevokedToken(jti=jti, expires_at=expires_at))
        self.db.commit()
