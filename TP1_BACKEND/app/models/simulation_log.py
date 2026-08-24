from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class SimulationLog(Base):
    __tablename__ = "simulation_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    model_version_id = Column(Integer, ForeignKey("ml_model_versions.id"), nullable=True)
    
    # Simulator Environment Inputs
    outdoor_temp = Column(Float, nullable=False)
    outdoor_rh = Column(Float, nullable=False)
    ahu_temp = Column(Float, nullable=False)
    ahu_rh = Column(Float, nullable=False)
    
    # Room State & Targets
    current_room_rh = Column(Float, nullable=False)
    target_setpoint = Column(Float, nullable=False)
    
    # Control Triad (Human-in-the-Loop)
    current_power = Column(Float, nullable=False)
    recommended_power = Column(Float, nullable=False)
    applied_power = Column(Float, nullable=False)
    
    # Regulatory Compliance
    action = Column(String(50), nullable=False)
    justification = Column(String(255), nullable=True)

    user = relationship("User", back_populates="simulations")
    model_version = relationship("MlModelVersion", back_populates="simulations")