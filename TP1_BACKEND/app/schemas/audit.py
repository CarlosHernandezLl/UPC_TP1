from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class AuditLogBase(BaseModel):
    user_id: int
    action: str
    module: str
    description: str
    payload: Optional[Any] = None

class AuditLogCreate(AuditLogBase):
    pass

class AuditLogResponse(AuditLogBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True