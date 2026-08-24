from sqlalchemy.orm import Session
from app.models.audit_trail import AuditTrail


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, log_data: dict) -> AuditTrail:
        # Convertir dict → objeto del modelo
        log = AuditTrail(**log_data)
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_all(self, limit: int = 500):
        return (
            self.db.query(AuditTrail)
            .order_by(AuditTrail.created_at.desc())
            .limit(limit)
            .all()
        )
