# app/models/plc.py
from sqlalchemy import Column, Integer, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class DataPLC(Base):
    # En Postgres, si no usaste comillas al crear la tabla, el nombre se guarda en minúsculas
    __tablename__ = "dataplc" 

    id = Column(Integer, primary_key=True, index=True)
    dato_real = Column(Numeric(5, 1))
    fecha = Column(DateTime, server_default=func.now())