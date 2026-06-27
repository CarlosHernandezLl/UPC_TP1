from pydantic import BaseModel, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional

class GmpParameterBase(BaseModel):
    min_hum_limit: float
    max_hum_limit: float
    default_setpoint: Optional[float] = 50.0

class GmpParameterUpdate(BaseModel):
    min_hum_limit: float
    max_hum_limit: float
    default_setpoint: Optional[float] = None

    @field_validator('max_hum_limit')
    @classmethod
    def validate_limits(cls, v: float, info: ValidationInfo):
        if 'min_hum_limit' in info.data and v <= info.data['min_hum_limit']:
            raise ValueError("El límite máximo debe ser mayor al mínimo")
        return v

class GmpParameterResponse(GmpParameterBase):
    id: int
    updated_at: datetime
    updated_by: Optional[int]

    class Config:
        from_attributes = True