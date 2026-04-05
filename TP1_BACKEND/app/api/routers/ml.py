from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ml_service import MLService
from app.schemas.ml import PredictionInput, PredictionOutput
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/ml", tags=["ml"])

@router.post("/simulate-train")
async def simulate_training(db: Session = Depends(get_db)):
    ml_service = MLService(db)
    metrics = await ml_service.train_model()
    return metrics


@router.post("/predict", response_model=PredictionOutput)
async def predict_consumption(data: PredictionInput):
    service = PredictionService()
    result = await service.predict_power(data)
    return {"potencia_estimada": round(result, 2)}