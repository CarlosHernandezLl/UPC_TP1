import xgboost as xgb
import joblib
import pandas as pd
import os

class MLEngine:
    def __init__(self):
        self.model_path = "models/hvac_model.joblib"
        os.makedirs("models", exist_ok=True)

    def train(self, data: list):
        # Convertimos la lista de registros de la BD a DataFrame
        df = pd.DataFrame(data)
        
        # Definimos las variables (Features y Target)
        # Asegúrate que los nombres coincidan con los que guarda tu DataService
        features = ['temp_ext', 'w_ext', 'temp_uma', 'w_uma', 'potencia_secador', 'temp_sala', 'hum_sala']
        target = 'w_sala' # Queremos predecir la humedad absoluta resultante en sala
        
        X = df[features]
        y = df[target]
        
        # Configuramos el modelo XGBoost
        model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.05,
            max_depth=6,
            objective='reg:squarederror'
        )
        
        model.fit(X, y)
        
        # Guardamos el modelo entrenado
        joblib.dump(model, self.model_path)
        return {"status": "success", "message": f"Modelo entrenado con {len(df)} registros"}

    def predict(self, input_data: dict):
        # En lugar de usar el modelo real, devolvemos un valor de prueba
        return {
            "recommended_w_sala": 0.0125, 
            "status": "mock_mode",
            "message": "Conexión exitosa desde el microservicio de ML"
        }
        
        # if not os.path.exists(self.model_path):
        #     return {"error": "Modelo no encontrado. Entrena primero."}
            
        # model = joblib.load(self.model_path)
        # # Convertimos el JSON de entrada a DataFrame de una fila
        # df_input = pd.DataFrame([input_data])
        # prediction = model.predict(df_input)
        
        # return {"recommended_w_sala": float(prediction[0])}