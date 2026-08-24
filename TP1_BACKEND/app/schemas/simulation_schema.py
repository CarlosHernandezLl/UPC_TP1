from typing import Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field


# 🚀 1. CLASE BASE: Telemetría climática y de planta que es común a ambos pasos
class SimulationBase(BaseModel):
    outdoor_temp: float = Field(..., description="Temperatura exterior (°C)")
    outdoor_rh: float = Field(
        ..., ge=0, le=100, description="Humedad relativa exterior (%)"
    )
    ahu_temp: float = Field(..., description="Temperatura de suministro UMA (°C)")
    ahu_rh: float = Field(..., ge=0, le=100, description="Humedad relativa UMA (%)")
    current_room_rh: Optional[float] = Field(
        50.0, ge=0, le=100, description="Humedad actual en sala limpia (%)"
    )
    target_setpoint: float = Field(
        ..., ge=0, le=100, description="Humedad relativa objetivo (%)"
    )
    current_power: float = Field(
        ..., ge=0, le=100, description="Potencia actual del PLC (%)"
    )


# 🎯 2. PAYLOAD PASO A: Lo que el frontend envía a POST /simulation/predict
class SimulationPredictRequest(SimulationBase):
    pass  # No requiere ningún campo extra, hereda todo de SimulationBase


# 🎯 3. PAYLOAD PASO B: Lo que el frontend envía a POST /simulation/log-action
class SimulationLogRequest(SimulationBase):
    recommended_power: float = Field(
        ..., ge=0, le=100, description="Potencia calculada por XGBoost (%)"
    )
    applied_power: float = Field(
        ..., ge=0, le=100, description="Potencia que el operador decidió aplicar (%)"
    )

    # Estandarización GxP en inglés técnico
    action: Literal["RECOMMENDATION_APPLIED", "RECOMMENDATION_OVERRIDDEN"] = Field(
        ..., description="Tipo de acción tomada por el operador"
    )
    justification: Optional[str] = Field(
        "N/A", description="Motivo técnico en caso de sobreescribir a la IA"
    )


# 🎯 4. RESPUESTA PASO A: Lo que devuelve el servidor al predecir
class SimulationPredictResponse(BaseModel):
    potencia_recomendada: float
    ahorro_estimado_pct: float
    alerta_gmp: bool
    explicacion_gemini: str
