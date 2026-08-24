from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    resource = Column(String(50), nullable=False)
    detail = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )

    user = relationship("User", back_populates="audit_actions")