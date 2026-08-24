from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class GmpParameter(Base):
    __tablename__ = "gmp_parameters"

    id = Column(Integer, primary_key=True, index=True)
    min_hum_limit = Column(Float, default=40.0)
    max_hum_limit = Column(Float, default=70.0)
    default_setpoint = Column(Float, default=49.0)
    updated_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("America/Lima")),
        onupdate=lambda: datetime.now(ZoneInfo("America/Lima"))
    )
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    updater = relationship("User", back_populates="gmp_updates")