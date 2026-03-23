from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, index=True)  # Quién realizó la acción
    action = Column(String)               # Ejemplo: "CAMBIO_SETPOINT", "LOGIN"
    module = Column(String)               # Ejemplo: "OPTIMIZADOR", "SEGURIDAD"
    description = Column(String)          # Detalle legible por humanos
    previous_value = Column(JSON, nullable=True) # Estado anterior
    new_value = Column(JSON, nullable=True)      # Estado nuevo
    payload = Column(JSON, nullable= True)