from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo
from typing import Optional
from datetime import datetime

class GmpParameterBase(BaseModel):
    min_hum_limit: float = Field(40.0, ge=0.0, le=100.0)
    max_hum_limit: float = Field(70.0, ge=0.0, le=100.0)
    default_setpoint: Optional[float] = Field(49.0, ge=0.0, le=100.0)

    @field_validator('max_hum_limit')
    @classmethod
    def validate_limits(cls, v: float, info: ValidationInfo):
        if 'min_hum_limit' in info.data and v <= info.data['min_hum_limit']:
            raise ValueError("El límite máximo higrométrico debe ser estrictamente mayor al mínimo")
        return v

class GmpParameterUpdate(GmpParameterBase):
    pass

class GmpParameterResponse(GmpParameterBase):
    id: int
    updated_at: datetime
    updated_by: int

    model_config = ConfigDict(from_attributes=True)