from pydantic import BaseModel
from typing import List

class OptimizationInput(BaseModel):
    # Variables que NO controlamos (Estado actual)
    temp_secador: float
    hum_secador: float
    temp_sala: float
    hum_sala: float
    temp_ext: float
    hum_ext: float
    potencia_actual: float

class OptimizationResult(BaseModel):
    temp_uma_optima: float
    hum_uma_optima: float
    potencia_minima_estimada: float
    ahorro_estimado: float # Diferencia con la potencia actual