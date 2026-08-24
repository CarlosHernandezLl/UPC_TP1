from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class AuditCreate(BaseModel):
    action: str = Field(..., max_length=50)
    resource: str = Field(..., max_length=50)
    detail: Optional[str] = None
    ip_address: Optional[str] = None


class AuditResponse(BaseModel):
    id: int
    action: str
    user: str
    timestamp: str
    details: str
