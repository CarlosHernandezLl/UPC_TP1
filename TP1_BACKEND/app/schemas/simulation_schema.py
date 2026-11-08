from typing import Optional
from typing_extensions import Literal
from pydantic import BaseModel, Field, model_validator

MIN_JUSTIFICATION_CHARS = 10


# 🚀 1. CLASE BASE: Telemetría climática y de planta que es común a ambos pasos
class SimulationBase(BaseModel):
    outdoor_temp: float = Field(
        ..., ge=0, le=50, description="Temperatura exterior (°C)"
    )
    outdoor_rh: float = Field(
        ..., ge=0, le=100, description="Humedad relativa exterior (%)"
    )
    ahu_temp: float = Field(
        ..., ge=0, le=50, description="Temperatura de suministro UMA (°C)"
    )
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
    room_temp: float = Field(
        ..., ge=0, le=50, description="Temperatura actual en sala limpia (°C)"
    )
    injection_pressure: float = Field(
        ..., ge=0, le=1000, description="Presión de inyección (Pa)"
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

    @model_validator(mode="after")
    def require_justification_when_overridden(self):
        """GxP: descartar la recomendación exige un sustento técnico de al menos 10 caracteres."""
        if self.action == "RECOMMENDATION_OVERRIDDEN":
            text = (self.justification or "").strip()
            if len(text) < MIN_JUSTIFICATION_CHARS or text.upper() == "N/A":
                raise ValueError(
                    "Por normativa GxP, debe ingresar una justificación técnica detallada "
                    f"(mínimo {MIN_JUSTIFICATION_CHARS} caracteres)."
                )
        return self


# 🎯 4. RESPUESTA PASO A: Lo que devuelve el servidor al predecir
class SimulationPredictResponse(BaseModel):
    potencia_recomendada: float
    ahorro_estimado_pct: float
    alerta_gmp: bool
    # Límites GMP con los que se evaluó la alerta (los vigentes en BD al momento de predecir)
    limite_min_gmp: float
    limite_max_gmp: float
    explicacion_gemini: str
