from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.ml_schema import PredictionInput, PredictionOutput
from pydantic import BaseModel
from app.models.ml_version_model import MlModelVersion, ModelStatus
from app.models.hvac_model import HvacHistoricalData
from app.services.ml_client_service import MLClient
import joblib
import pandas as pd
import numpy as np

router = APIRouter(prefix="/ml", tags=["ml"])

@router.post("/trigger-training")
async def trigger_training(db: Session = Depends(get_db)):
    # # 1. Obtenemos la data que ya registraste de los CSV
    data = db.query(HvacHistoricalData).all()
    
    # # 2. La formateamos a una lista de diccionarios
    records = []
    for d in data:
        rec = {
            "temp_ext": d.temp_ext,
            "w_ext": d.w_ext,
            "temp_uma": d.temp_uma,
            "w_uma": d.w_uma,
            "potencia_secador": d.potencia_secador,
            "temp_sala": d.temp_sala,
            "hum_sala": d.hum_sala,
            "w_sala": d.w_sala
        }
        # Reemplazar NaN por None (JSON lo convierte en null)
        for k, v in rec.items():
            if isinstance(v, float) and (pd.isna(v) or np.isinf(v)):
                rec[k] = None
            
        records.append(rec)
    
    # 3. Se la enviamos al microservicio (puerto 8001)
    response = await MLClient.train_model(records)
    
    return {
        "status": "Comunicación establecida",
        "ml_service_response": response
    }
    
    # # Simulación de respuesta exitosa
    # return {
    #     "status": "Comunicación establecida",
    #     "ml_service_response": {
    #         "status": "success",
    #         "message": "Modelo entrenado con 1000 registros"
    #     }
    # }