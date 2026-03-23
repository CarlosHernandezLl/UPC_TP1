from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from datetime import datetime
# from app.schemas.hvac import  

class HVACReading(Base):
    __tablename__ = "hvac_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    #Variables de proceso
    humedad_secador = Column(Float, nullable=False)
    temperatura_secador = Column(Float, nullable=False)
    temperatura_inyeccion = Column(Float, nullable=False)
    
    #Variables de Restriccion GxP (Calidad)
    temperatura_sala = Column(Float, nullable=False)
    humedad_sala = Column(Float, nullable = False)
    
    #Variable Objetivo
    potencia_secador = Column(Float, nullable= False)
    
    #Variable de Perturbación (Exterior)
    temperatura_exterior = Column(Float, nullable= False)
    humedad_exterior = Column(Float, nullable= False)
    
    #Campos de Auditoría INF03
    device_id = Column(String, nullable=True)
    is_estimated = Column(Boolean, default=False)
    