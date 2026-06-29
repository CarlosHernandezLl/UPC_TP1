from app.repositories.audit_repository import AuditRepository
from app.models.audit_model import AuditTrail
from typing import List
from datetime import datetime
from zoneinfo import ZoneInfo

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def register_operator_action(self, user_id: int, action: str, detail: str):
        # Creamos el objeto AuditTrail que tu repositorio solicita en 'create_log'
        new_log = AuditTrail(
            user_id=user_id,
            action=action,
            resource="HVAC_SIMULATOR",
            detail=detail,
            created_at=datetime.now(ZoneInfo("America/Lima"))
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
            
            if log.created_at:
                timestamp_str = log.created_at.strftime("%d/%m/%Y %H:%M:%S")
            else:
                timestamp_str = "N/A"
            
            formatted_logs.append({
                "id": log.id,
                "action": log.action,
                "user": user_name,
                "timestamp": timestamp_str,
                "details": log.detail
            })
            
        return formatted_logs
    
    def record_action(self, user_id: int, action: str, resource: str, detail: str):
        """Método polimórfico global para auditoría inmutable (21 CFR Part 11)"""
        new_log = AuditTrail(
            user_id=user_id,
            action=action,
            resource=resource,  # 🚀 Ahora el recurso es dinámico (ej: CONFIG_MODULE)
            detail=detail,
            created_at=datetime.now(ZoneInfo("America/Lima"))
        )
        return self.repository.create_log(new_log)