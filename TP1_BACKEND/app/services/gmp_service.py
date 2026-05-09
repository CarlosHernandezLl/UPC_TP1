from app.repositories.gmp_repository import GmpRepository
from app.services.audit_service import AuditService

class GmpService:
    def __init__(self, repository: GmpRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service

    def update_gmp_config(self, user_id: int, config_data: dict):
        updated_params = self.repository.update_parameters(user_id, config_data)
        
        self.audit_service.record_action(
            user_id=user_id,
            action="GMP_LIMITS_UPDATE",
            resource="CONFIG_MODULE",
            detail=f"Límites actualizados: Min={config_data['min_hum_limit']}%, Max={config_data['max_hum_limit']}%",
            ip="127.0.0.1"
        )
        
        return updated_params