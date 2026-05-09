from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from app.core.database import Base
import sqlalchemy.orm as orm
from sqlalchemy.sql import func

# --- CONFIGURACIÓN Y PARÁMETROS GMP ---
class GmpParameter(Base):
    __tablename__ = "gmp_parameters"

    id = Column(Integer, primary_key=True)
    min_hum_limit = Column(Float, default=40.0)
    max_hum_limit = Column(Float, default=70.0)
    default_setpoint = Column(Float, default=49.0)
    updated_at = Column(DateTime, onupdate=func.now(), server_default=func.now())
    updated_by = Column(Integer, ForeignKey("users.id"))