from app.repositories.audit_repository import AuditRepository
from app.models.audit_model import AuditTrail

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def record_action(self, user_id: int, action: str, resource: str, detail: str, ip: str = None):
        """
        Método universal para registrar cualquier acción en el sistema.
        """
        new_log = AuditTrail(
            user_id=user_id,
            action=action,
            resource=resource,
            detail=detail,
            ip_address=ip
        )
        return self.repository.create_log(new_log)

    def get_report_data(self):
        logs = self.repository.get_all_logs()
        # Mapeo manual para asegurar que el frontend reciba el full_name del usuario
        for log in logs:
            log.user_full_name = log.user.full_name
        return logs