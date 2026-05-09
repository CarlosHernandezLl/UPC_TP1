from app.core.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Boolean, BigInteger, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func

class SystemError(Base):
    __tablename__ = "system_errors"

    id = Column(Integer, primary_key=True)
    module = Column(String(50)) # ML_ENGINE, API, DATA_MERGE
    error_msg = Column(Text)
    stack_trace = Column(Text)
    created_at = Column(DateTime, server_default=func.now())