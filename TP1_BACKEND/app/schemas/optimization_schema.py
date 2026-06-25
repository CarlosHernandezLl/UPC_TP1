from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class OptimizationLogCreate(BaseModel):
    # 1. Entorno Exterior
    temp_ext: float
    hum_ext: float
    
    # 2. Entrada de Aire (UMA)
    temp_uma: float
    hum_uma: float
    
    # 3. Estado de la Sala (¡Aquí está la corrección!)
    hum_sala_actual: float  # 🆕 ¡Faltaba esta variable crítica!
    setpoint_humedad: float
    potencia_actual: float
    
    # 4. Resultados de la IA y Acción del Operador
    potencia_recomendada: float
    potencia_aplicada: float
    accion: str  # "RECOMENDACION_APLICADA", "RECOMENDACION_IGNORADA", etc.
    justificacion: Optional[str] = None

class OptimizationLogResponse(OptimizationLogCreate):
    id: int
    timestamp: datetime
    user_id: int

    class Config:
        from_attributes = True