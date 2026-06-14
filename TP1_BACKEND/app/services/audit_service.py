from app.repositories.audit_repository import AuditRepository
from app.models.audit_model import AuditTrail
from typing import List

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def register_operator_action(self, user_id: int, action: str, detail: str):
        # Creamos el objeto AuditTrail que tu repositorio solicita en 'create_log'
        new_log = AuditTrail(
            user_id=user_id,
            action=action,
            resource="HVAC_SIMULATOR",
            detail=detail
            # created_at se genera automáticamente en la BD por defecto
        )
        # Llamamos a tu método exacto del repositorio
        return self.repository.create_log(new_log)

    def get_report_data(self) -> List[dict]:
        # Llamamos a tu método exacto que hace el .join(User)
        db_logs = self.repository.get_all_logs()
        
        formatted_logs = []
        for log in db_logs:
            # Asumiendo que en tu modelo AuditTrail tienes una relación configurada 'user' 
            # (ej. user = relationship("User")), podemos extraer el full_name directamente.
            # Si no hay relación, la propiedad se accede mediante la unión automática de SQLAlchemy.
            user_name = log.user.full_name if hasattr(log, 'user') and log.user else "Usuario Desconocido"
            
            formatted_logs.append({
                "id": log.id,
                "action": log.action,
                "user": user_name,
                "timestamp": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "N/A",
                "details": log.detail
            })
            
        return formatted_logs