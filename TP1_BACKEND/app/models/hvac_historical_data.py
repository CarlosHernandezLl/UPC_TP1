import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class HvacHistoricalData(Base):
    __tablename__ = "hvac_historical_data"

    id = Column(BigInteger, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(ZoneInfo("America/Lima")),
    )
    batch_id = Column(
        UUID(as_uuid=True), default=uuid.uuid4, nullable=False, index=True
    )

    # Outdoor Environment
    outdoor_temp = Column(Float)
    outdoor_w = Column(Float)

    # AHU (Air Handling Unit)
    ahu_temp = Column(Float)
    ahu_w = Column(Float)

    # Control and Process
    dryer_power = Column(Float)
    room_temp = Column(Float)
    room_rh = Column(Float)
    room_w = Column(Float)

    is_clean = Column(Boolean, default=True)
