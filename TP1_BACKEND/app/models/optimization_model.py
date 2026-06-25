from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class OptimizationLog(Base):
    __tablename__ = "optimization_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id")) # Trazabilidad de quién operó
    
    # Variables del entorno del Simulador
    temp_ext = Column(Float)
    hum_ext = Column(Float)
    temp_uma = Column(Float)
    hum_uma = Column(Float)
    
    # 🆕 CORRECCIÓN: Columna crítica para el estado de la sala
    hum_sala_actual = Column(Float)        # ¡Agregado para el match con la pantalla!
    setpoint_humedad = Column(Float)       # Setpoint Objetivo (%)
    
    # Datos críticos para la gráfica comparativa (Dashboard)
    potencia_actual = Column(Float)        # Lo que tenía la UMA antes
    potencia_recomendada = Column(Float)   # Lo que calculó el XGBoost (Ideal)
    potencia_aplicada = Column(Float)      # Lo que el usuario digitó finalmente (Real)
    
    # Cumplimiento normativo
    accion = Column(String)                # "RECOMENDACION_APLICADA" o "RECOMENDACION_MODIFICADA"
    justificacion = Column(String, nullable=True) # Obligatorio si el operador no le hizo caso a la IA