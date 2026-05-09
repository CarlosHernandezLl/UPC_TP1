from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, JSON, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

# --- OPERACIÓN Y SIMULACIÓN ---
class SimulationLog(Base):
    __tablename__ = "simulation_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("ml_model_versions.id"))
    
    # Guardamos los inputs en formato JSON para no tener mil columnas
    input_json = Column(JSON) 
    
    recommended_p = Column(Float)
    manual_p = Column(Float)
    predicted_hum = Column(Float)
    
    was_applied = Column(Boolean, default=False)
    discard_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="simulations")
    model = relationship("MlModelVersion", back_populates="simulations")