from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class AuditResponse(BaseModel):
    id: int
    user_id: int
    action: str
    resource: str
    detail: str
    ip_address: Optional[str]
    created_at: datetime
    
    user_full_name: Optional[str] = None 

    model_config = ConfigDict(from_attributes=True)

class AuditCreate(BaseModel):
    action: str
    resource: str
    detail: str
    user_id: int
    ip_address: Optional[str] = None