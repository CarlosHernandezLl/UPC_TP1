from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from app.core.database import Base

class EnergyPricing(Base):
    __tablename__ = "energy_pricing"

    id = Column(Integer, primary_key=True, index=True)
    kwh_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    is_active = Column(Boolean, default=True)
    effective_from = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )