from app.core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, BigInteger, Integer, String, Boolean, Float, DateTime, Enum, ForeignKey, JSON, Text
from enum import Enum as PyEnum
from sqlalchemy.sql import func

class ModelStatus(PyEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class MlModelVersion(Base):
    __tablename__ = "ml_model_versions"

    id = Column(Integer, primary_key=True)
    version_tag = Column(String(20), unique=True)
    model_path = Column(String(255)) # Ruta al .joblib
    r2_score = Column(Float)
    rmse = Column(Float)
    trained_at = Column(DateTime, server_default=func.now())
    status = Column(Enum(ModelStatus), default=ModelStatus.ARCHIVED)

    simulations = relationship("SimulationLog", back_populates="model")