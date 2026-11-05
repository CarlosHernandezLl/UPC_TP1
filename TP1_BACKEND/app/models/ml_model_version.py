from enum import Enum as PyEnum
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class ModelStatus(PyEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class MlModelVersion(Base):
    __tablename__ = "ml_model_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_tag = Column(String(20), unique=True, nullable=False)
    model_path = Column(String(255), nullable=False)
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    r2_score = Column(Float)
    rmse = Column(Float)
    # Impacto SHAP medio por variable: [{"feature": str, "shap": float}, ...] ordenado de mayor a menor
    feature_importance = Column(JSON, nullable=True)
    trained_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )
    status = Column(Enum(ModelStatus), default=ModelStatus.ARCHIVED)

    simulations = relationship("SimulationLog", back_populates="model_version")
