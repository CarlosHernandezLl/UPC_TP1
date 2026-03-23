# app/models/raw_data.py
from sqlalchemy import Column, Integer, Float, DateTime
from app.core.database import Base

class RawPlcData(Base):
    __tablename__ = "raw_plc_data"
    # id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key= True, index=True)
    temp_secador = Column(Float)
    hum_secador = Column(Float)
    temp_uma = Column(Float)
    hum_uma = Column(Float)
    potencia = Column(Float)

class RawDataloggerData(Base):
    __tablename__ = "raw_datalogger_data"
    # id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key= True, index=True)
    temp_sala = Column(Float)
    hum_sala = Column(Float)

class RawWeatherData(Base):
    __tablename__ = "raw_weather_data"
    # id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, primary_key = True, index=True)
    temp_ext = Column(Float)
    hum_ext = Column(Float)