from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class HvacReadingCreate(BaseModel):
    humedad_secador: float
    temperatura_secador: float
    temperatura_inyeccion: float
    temperatura_sala: float
    humedad_sala: float
    potencia_secador: float
    temperatura_exterior: float
    humedad_exterior: float
    device_id: str
    is_estimated: Optional[bool] = False

class HvacReadingResponse(HvacReadingCreate):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True