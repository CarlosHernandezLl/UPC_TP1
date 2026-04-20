import joblib
import os
import pandas as pd # Importante añadir pandas
import numpy as np
from app.schemas.ml import PredictionInput

class PredictionService:
    def __init__(self):
        self.model_path = os.path.join("app", "ml", "hvac_model.pkl")
        self.model = None

    def _load_model(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("El modelo entrenado no existe. Ejecuta el entrenamiento primero.")
        self.model = joblib.load(self.model_path)

    async def predict_power(self, data: PredictionInput):
        if self.model is None:
            self._load_model()
        
        # 1. Definir los nombres de las columnas EXACTAMENTE como se usaron en el entrenamiento
        # Si en tu MLService usaste 't_secador', 'h_secador', etc., pon esos aquí.
        """feature_names = [
            "temp_secador", "hum_secador",
            "temp_uma", "hum_uma", 
            "temp_sala", "hum_sala",
            "temp_ext", "hum_ext"
        ]"""
        
        delta_calculado = data.hum_uma - data.hr_target
        
        feature_names = [
            "temp_uma", "hum_uma", 
            "temp_ext", "hum_ext",
            "hr_target", "delta_h"  # Este es el 'norte' que guía la recomendación
        ]
        
        # 2. Crear un DataFrame con una sola fila
        # Esto mapea tus campos del esquema (temp_secador) a los del modelo (t_secador)
        """input_df = pd.DataFrame([[
            data.temp_secador, data.hum_secador, 
            data.temp_uma, data.hum_uma,
            data.temp_sala, data.hum_sala, 
            data.temp_ext, data.hum_ext
        ]], columns=feature_names)
        """
        input_df = pd.DataFrame([[
            data.temp_uma, 
            data.hum_uma,
            data.temp_ext, 
            data.hum_ext,
            data.hr_target,
            delta_calculado
        ]], columns=feature_names)
        
        # 3. Realizar la predicción usando el DataFrame
        prediction = self.model.predict(input_df)
        
        recommended_power = max(0, min(100, float(prediction[0])))
        
        return recommended_power