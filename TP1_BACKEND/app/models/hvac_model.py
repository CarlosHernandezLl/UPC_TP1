from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float, DateTime
from app.core.database import Base
from sqlalchemy.orm import relationship

# --- INTELIGENCIA Y DATOS HISTÓRICOS ---
class HvacHistoricalData(Base):
    __tablename__ = "hvac_historical_data"

    id = Column(BigInteger, primary_key=True, index=True)
    # El timestamp es crítico para el merge_asof de tus 3 archivos
    timestamp = Column(DateTime, nullable=False, index=True)
    
    # Ambiente
    temp_ext = Column(Float)
    w_ext = Column(Float) # Humedad absoluta calculada
    
    # UMA
    temp_uma = Column(Float)
    w_uma = Column(Float) # Humedad absoluta calculada
    
    # Control y Proceso
    potencia_secador = Column(Float)
    temp_sala = Column(Float)
    hum_sala = Column(Float) # Humedad relativa (Target)
    w_sala = Column(Float)
    
    is_clean = Column(Boolean, default=True)