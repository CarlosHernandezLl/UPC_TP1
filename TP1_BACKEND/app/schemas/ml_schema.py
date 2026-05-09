from pydantic import BaseModel

class PredictionInput(BaseModel):
    #temp_secador: float
    #hum_secador: float
    temp_uma: float
    hum_uma: float
    #temp_sala: float
    hr_target: float
    temp_ext: float
    hum_ext: float

class PredictionOutput(BaseModel):
    potencia_estimada: float
    unidad: str = "kW" # o % según tu escala