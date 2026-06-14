from pydantic import BaseModel
from datetime import datetime

class AuditResponse(BaseModel):
    id: int
    action: str
    user: str
    timestamp: str
    details: str

    class Config:
        from_attributes = True

class AuditCreate(BaseModel):
    action: str
    detail: str