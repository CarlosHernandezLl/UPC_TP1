from fastapi import FastAPI, HTTPException
from model_engine import MLEngine
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Microservicio de ML - HVAC")
engine = MLEngine()

# Schema para recibir los datos de entrenamiento
class TrainRequest(BaseModel):
    records: List[dict]

@app.post("/train-v1")
async def train(request: TrainRequest):
    if not request.records:
        raise HTTPException(status_code=400, detail="No hay datos para entrenar")
    return engine.train(request.records)

@app.post("/predict-v1")
async def predict(data: dict):
    return engine.predict(data)


@app.post("/train")
async def train(payload: dict):
    records = payload.get("records", [])
    return {"message": "Recibí los registros", "count": len(records)}

@app.post("/predict")
async def predict(payload: dict):
    return {"prediction": "dummy_result", "input": payload}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)