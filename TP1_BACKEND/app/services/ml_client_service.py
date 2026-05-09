import httpx

ML_SERVICE_URL = "http://localhost:8001"

class MLClient:
    @staticmethod
    async def train_model(historical_data: list):
        async with httpx.AsyncClient() as client:
            # Enviamos los datos de la BD al microservicio
            response = await client.post(
                f"{ML_SERVICE_URL}/train", 
                json={"records": historical_data},
                timeout=None # El entrenamiento puede tardar
            )
            return response.json()

    @staticmethod
    async def get_prediction(current_state: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ML_SERVICE_URL}/predict", 
                json=current_state
            )
            return response.json()