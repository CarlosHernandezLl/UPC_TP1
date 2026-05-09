from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from app.core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class EnergyPricing(Base):
    __tablename__ = "energy_pricing"

    id = Column(Integer, primary_key=True)
    kwh_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime, server_default=func.now())