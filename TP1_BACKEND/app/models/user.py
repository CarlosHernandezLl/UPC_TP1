from enum import Enum as PyEnum
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(PyEnum):
    ADMIN = "ADMIN"
    SUPERVISOR = "SUPERVISOR"
    AUDITOR = "AUDITOR"
    GERENTE = "GERENTE"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.SUPERVISOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )
    
    simulations = relationship("SimulationLog", back_populates="user")
    audit_actions = relationship("AuditTrail", back_populates="user")
    gmp_updates = relationship("GmpParameter", back_populates="updater")