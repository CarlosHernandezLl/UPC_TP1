from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class HvacReadingCreate(BaseModel):
    batch_id: str = Field(..., min_length=1, max_length=50)
    outdoor_temp: float
    outdoor_w: float
    ahu_temp: float
    ahu_w: float
    dryer_power: float = Field(..., ge=0.0, le=100.0)
    room_temp: float
    room_rh: float = Field(..., ge=0.0, le=100.0)
    room_w: float
    is_clean: Optional[bool] = True


class HvacReadingResponse(HvacReadingCreate):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
