from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogCreate

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, audit_in: AuditLogCreate) -> AuditLog:
        db_obj = AuditLog(
            user_id=audit_in.user_id,
            action=audit_in.action,
            module=audit_in.module,
            description=audit_in.description,
            payload=audit_in.payload
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_logs(self, skip: int = 0, limit: int = 100):
        return self.db.query(AuditLog).offset(skip).limit(limit).all()