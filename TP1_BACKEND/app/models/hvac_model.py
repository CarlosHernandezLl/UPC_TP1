import datetime
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float, DateTime
from datetime import datetime
from sqlalchemy.sql import func
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


class DataIngestionLog(Base):
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    fecha_carga = Column(DateTime(timezone=True), server_default=func.now())
    rango_datos = Column(String(50), nullable=False)  # Guarda ej: "23/04 - 25/04"
    registros = Column(Integer, nullable=False)       # Filas totales procesadas en el merge_asof
    estado = Column(String(30), nullable=False)       # "SINCRONIZADO" o "ERROR"