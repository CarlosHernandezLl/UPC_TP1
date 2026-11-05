from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
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

    def get_all(
        self, limit: int = 500, desde: date | None = None, hasta: date | None = None
    ):
        """Eventos más recientes; `desde`/`hasta` (inclusivos, hora de Lima) acotan el rango."""
        lima = ZoneInfo("America/Lima")
        query = self.db.query(AuditTrail)
        if desde:
            query = query.filter(
                AuditTrail.created_at >= datetime.combine(desde, time.min, tzinfo=lima)
            )
        if hasta:
            query = query.filter(
                AuditTrail.created_at
                < datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=lima)
            )
        return query.order_by(AuditTrail.created_at.desc()).limit(limit).all()

    def get_by_resource(self, resource: str, limit: int = 100):
        return (
            self.db.query(AuditTrail)
            .filter(AuditTrail.resource == resource)
            .order_by(AuditTrail.created_at.desc())
            .limit(limit)
            .all()
        )
