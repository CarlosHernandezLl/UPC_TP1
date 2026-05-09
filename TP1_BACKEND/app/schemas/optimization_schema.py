from pydantic import BaseModel
from typing import List

class OptimizationInput(BaseModel):
    # Variables que NO controlamos (Estado actual)
    #temp_sala: float
    #hum_sala: float
    temp_uma: float
    hum_uma: float
    temp_ext: float
    hum_ext: float
    setpoint_max: float = 50.0

class OptimizationResult(BaseModel):
    temp_uma_optima: float
    hum_uma_optima: float
    potencia_minima_estimada: float
    ahorro_estimado: float # Diferencia con la potencia actual