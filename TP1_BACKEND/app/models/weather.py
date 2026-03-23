from sqlalchemy import Column, Integer, Float, DateTime
from app.core.database import Base
from datetime import datetime

class RawExternalWeather(Base):
    __tablename__ = "raw_external_weather"

    # id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    temp_ext = Column(Float, nullable=False)
    hum_ext = Column(Float, nullable=False)