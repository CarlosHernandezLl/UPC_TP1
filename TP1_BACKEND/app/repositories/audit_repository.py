from sqlalchemy.orm import Session
from app.models.audit_model import AuditTrail
from app.models.users_model import User

class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_log(self, log_data: AuditTrail):
        self.db.add(log_data)
        self.db.commit()
        self.db.refresh(log_data)
        return log_data

    def get_all_logs(self):
        return self.db.query(AuditTrail).join(User).order_by(AuditTrail.created_at.desc()).all()

    def filter_by_action(self, action: str):
        return self.db.query(AuditTrail).filter(AuditTrail.action == action).all()