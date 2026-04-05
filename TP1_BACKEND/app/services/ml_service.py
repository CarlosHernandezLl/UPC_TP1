"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sqlalchemy.orm import Session
from app.repositories.hvac_repository import HvacRepository
import joblib # Para guardar el modelo
import os

class MLService:
    def __init__(self, db: Session):
        self.repository = HvacRepository(db)

    async def train_and_test_model(self):
        # 1. Obtener datos de la base de datos
        readings = self.repository.get_latest_readings(limit=1000)
        if len(readings) < 50:
            return {"error": "Insuficientes datos para simular (mínimo 50)"}

        # 2. Convertir a DataFrame de Pandas
        data = [r.__dict__ for r in readings]
        df = pd.DataFrame(data)

        # 3. Selección de variables (Las 8 variables que definimos)
        features = [
            'temperatura_secador', 'humedad_secador', 'temperatura_inyeccion',
            'temperatura_sala', 'humedad_sala', 'temperatura_exterior', 'humedad_exterior'
        ]
        target = 'potencia_secador'

        X = df[features]
        y = df[target]

        # 4. Dividir datos (80% entrenamiento, 20% prueba para métricas)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # 5. Entrenar Modelo
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # 6. Predicción y Métricas
        predictions = model.predict(X_test)
        mse = mean_squared_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        # 7. Guardar el modelo físico para usarlo después
        model_path = os.path.join("app", "ml", "hvac_model_v1.pkl")
        joblib.dump(model, model_path)

        return {
            "r2_score": round(r2, 4),
            "mse": round(mse, 4),
            "samples_used": len(df),
            "status": "Modelo entrenado y guardado con éxito"
        }
        
        
        
"""        
import pandas as pd
from sqlalchemy.orm import Session
from app.models.raw_data import RawPlcData, RawDataloggerData, RawWeatherData
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import os

class MLService:
    def __init__(self, db: Session):
        self.db = db

    async def prepare_unified_dataset(self):
        # 1. Extraer datos de las 3 tablas
        plc_query = self.db.query(RawPlcData).all()
        dl_query = self.db.query(RawDataloggerData).all()
        weather_query = self.db.query(RawWeatherData).all()

        # 2. Convertir a DataFrames y asegurar que el timestamp sea tipo datetime
        df_plc = pd.DataFrame([vars(r) for r in plc_query]).drop(columns=['_sa_instance_state'])
        df_dl = pd.DataFrame([vars(r) for r in dl_query]).drop(columns=['_sa_instance_state'])
        df_weather = pd.DataFrame([vars(r) for r in weather_query]).drop(columns=['_sa_instance_state'])

        # Ordenar por tiempo (crítico para merge_asof)
        df_plc = df_plc.sort_values('timestamp')
        df_dl = df_dl.sort_values('timestamp')
        df_weather = df_weather.sort_values('timestamp')

        # 3. Fusión Inteligente (Alinear Datalogger y Clima al tiempo del PLC)
        # merge_asof busca el registro más cercano en el tiempo sin ser exacto
        unified_df = pd.merge_asof(
            df_plc, 
            df_dl, 
            on='timestamp', 
            direction='nearest', 
            tolerance=pd.Timedelta('1 minute') # Tolerancia de 1 min entre sensores
        )
        
        unified_df = pd.merge_asof(
            unified_df, 
            df_weather, 
            on='timestamp', 
            direction='nearest'
        )

        return unified_df.dropna() # Eliminar filas donde no se pudo alinear nada

    async def train_model(self):
        df = await self.prepare_unified_dataset()
        print(df.columns)
        
        if len(df) < 50:
            return {"error": "Insuficientes datos unificados"}

        # 4. Definir X (Entradas) e y (Salida)
        # Aquí ya tienes las 8 variables juntas en el mismo DataFrame
        X = df[['temp_secador', 'hum_secador',
        'temp_uma', 'hum_uma',
        'temp_sala', 'hum_sala',
        'temp_ext', 'hum_ext']]
        
        y = df['potencia']

        # 5. Entrenamiento
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)

        # 6. Guardar el modelo en la carpeta app/ml/
        os.makedirs("app/ml", exist_ok=True)
        joblib.dump(model, "app/ml/hvac_model.pkl")

        return {
            "r2_score": r2_score(y, model.predict(X)),
            "total_records": len(df),
            "status": "Modelo entrenado con datos de 3 fuentes"
        }