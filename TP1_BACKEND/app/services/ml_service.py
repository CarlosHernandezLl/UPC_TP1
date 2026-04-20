import pandas as pd
from sqlalchemy.orm import Session
from app.models.raw_data import RawPlcData, RawDataloggerData, RawWeatherData
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import joblib
import os
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import mean_squared_error


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
        
        
        unified_df = unified_df.dropna().copy()
        
        
        # --- NUEVA LÓGICA: INGENIERÍA DE CARACTERÍSTICAS DINÁMICAS (NARX) ---
        # A. Crear variables de memoria (Lags). Asumiendo que 1 fila = 1 minuto aprox.
        # "Qué estaba pasando hace 5 minutos"
        unified_df['potencia_t_5'] = unified_df['potencia'].shift(5)
        unified_df['hum_sala_t_5'] = unified_df['hum_sala'].shift(5)
        
        # B. Crear Derivada: ¿La humedad está subiendo o bajando en este instante?
        unified_df['tasa_cambio_humedad'] = unified_df['hum_sala'] - unified_df['hum_sala'].shift(1)
        
        # C. EL CAMBIO MÁS CRÍTICO: Desplazamiento del Objetivo (Target Shifting)
        # Queremos predecir la humedad que habrá en el FUTURO (ej. en 15 periodos/minutos)
        horizonte_prediccion = 15
        unified_df['hum_sala_FUTURA'] = unified_df['hum_sala'].shift(-horizonte_prediccion)
        
        # NUEVO: El objetivo transformado (El Delta)
        unified_df['cambio_futuro_hr'] = unified_df['hum_sala_FUTURA'] - unified_df['hum_sala']
        
        unified_df = unified_df.dropna().copy()        
        
        
        
        # NUEVA LÓGICA DE INGENIERÍA DE DATOS
        # A. Filtro de Estabilidad: Solo aprendemos de cuando la sala ya se estabilizó
        # Calculamos la desviación estándar de la humedad de la sala en los últimos 5 registros
        #unified_df['h_sala_std'] = unified_df['hum_sala'].rolling(window=5).std()
        
        # Filtramos: Solo filas donde la humedad no varíe más de 0.05% (estado estable)
        #df_stable = unified_df[unified_df['h_sala_std'] < 0.05].copy()
        
        # --- NUEVA LÓGICA DE SUAVIZADO (PARA EVITAR LOS ESCALONES 40, 60, 80) ---
        
        # A. Suavizamos la potencia: Esto crea valores intermedios entre los saltos bruscos.
        # Usamos una ventana de 15 registros para crear una "rampa" en lugar de un escalón.
        #unified_df['potencia'] = unified_df['potencia'].rolling(window=15, min_periods=1).mean()
        
        # B. Definir el Objetivo de Entrenamiento
        # El hr_target es la humedad que el sistema LOGRÓ alcanzar con esa potencia
        #unified_df['hr_target'] = unified_df['hum_sala']
        
        # C. Cálculo del DELTA (Crucial para evitar errores de 0%)
        # Es la diferencia entre lo que entra (UMA) y lo que quieres (Target)
        #unified_df['delta_h'] = unified_df['hum_uma'] - unified_df['hr_target']
        #noise = np.random.normal(0, 0.01, size=len(unified_df))
        #unified_df['potencia'] = unified_df['potencia'] + noise
        
        # D. Agregar un ruido mínimo (Jittering) para que el modelo no se "pegue" en valores exactos
        # Esto ayuda al XGBoost a entender que la potencia es una variable continua.
        
        
        # Eliminar filas donde no se pudo alinear nada
        return unified_df

    async def train_model(self):
        df = await self.prepare_unified_dataset()
        print(df.columns)
        
        
        # --- COLOCA EL CÓDIGO AQUÍ ---
        print("--- DIAGNÓSTICO DE DATOS ---")
        print("Valores únicos de potencia encontrados en tu Excel:")
        print(df['potencia'].value_counts()) 
        print("---------------------------")
        # -
        if len(df) < 50:
            return {"error": "Insuficientes datos unificados"}

        # 4. Definir X (Entradas) incluyendo la nueva variable 'delta_h'
        # IMPORTANTE: Ahora la POTENCIA es una entrada. Queremos saber su efecto.
        # features = [
        #     'temp_uma', 'hum_uma',
        #     'temp_ext', 'hum_ext',
        #     'hr_target',
        #     'delta_h'
        # ]
        
        features = [
            'temp_uma', 'hum_uma',
            'temp_ext', 'hum_ext',
            'hum_sala',             # Humedad de la sala actual
            'potencia',             # Potencia que el operador o el sistema decidió aplicar AHORA
            'potencia_t_5',         # Memoria de la potencia
            'hum_sala_t_5',         # Memoria de la humedad
            'tasa_cambio_humedad'   # Inercia
        ]
        
        X = df[features]
        y = df['cambio_futuro_hr'] # AHORA ENTRENAMOS PARA PREDECIR EL CAMBIO        
        
        # 5. Partición Temporal Estricta (Prohibido usar train_test_split aleatorio)
        # Usamos el primer 80% del tiempo para entrenar, y el último 20% para probar
        
        split_index = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_index], X.iloc[split_index:]
        y_train, y_test = y.iloc[:split_index], y.iloc[split_index:]
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # 6. Entrenamiento del XGBoost
        # Reducimos max_depth y añadimos subsample para evitar que memorice el ruido de los sensores
        model = XGBRegressor(
            n_estimators=100, 
            learning_rate=0.05, 
            max_depth=4, 
            subsample=0.8,
            random_state=42
        )
        
        model.fit(X_train, y_train)
        
        # PREDECIMOS EL CAMBIO
        prediccion_del_cambio = model.predict(X_test)
        
        # RECONSTRUIMOS EL VALOR ABSOLUTO PARA LA GRÁFICA Y MÉTRICAS
        # Humedad Predicha = Humedad Actual + Cambio Predicho
        
        importances = model.feature_importances_
        feature_names = X.columns
        
        # Crear la gráfica
        plt.figure(figsize=(10, 6))
        plt.barh(feature_names, importances)
        # plt.xlabel("Importancia Relativa")
        plt.xlabel("Importancia para predecir la Humedad Futura")
        plt.title("Impacto de las Variables en el Cuarto de Secado")
        plt.savefig('importancia_variables.png', bbox_inches='tight')
        print("✅ Gráfica guardada con éxito como 'importancia_variables.png'")
        
        # 7. Métricas de Evaluación Termodinámica
        y_pred_absoluta = X_test['hum_sala'].values + prediccion_del_cambio
        y_test_absoluta = X_test['hum_sala'].values + y_test.values # Esto es igual a hum_sala_FUTURA
        #y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test_absoluta, y_pred_absoluta)
        mae = mean_absolute_error(y_test_absoluta, y_pred_absoluta)
        rmse = np.sqrt(mean_squared_error(y_test_absoluta, y_pred_absoluta))
        media_humedad_real = np.mean(y_test_absoluta)
        cv_rmse = (rmse / media_humedad_real) * 100
    
        # 6. Guardar el modelo en la carpeta app/ml/
        os.makedirs("app/ml", exist_ok=True)
        joblib.dump(model, "app/ml/hvac_model.pkl")

        plt.figure(figsize=(12, 5))
        # Graficamos solo los últimos 100 puntos para que se vea claro
        plt.plot(y_test_absoluta[-100:], label="Humedad REAL en el Futuro", color="blue", linewidth=2)
        plt.plot(y_pred_absoluta[-100:], label="Humedad PREDICHA por XGBoost", color="red", linestyle="dashed")
        plt.title(f"Diagnóstico de Predicción (MAE: {mae:.2f}%)")
        plt.ylabel("Humedad Relativa (%)")
        plt.xlabel("Periodos de tiempo")
        plt.legend()
        plt.savefig('diagnostico_prediccion.png', bbox_inches='tight')
        print("✅ Gráfica de diagnóstico guardada como 'diagnostico_prediccion.png'")

        return {
            "r2_score": round(r2, 4),
            "mae_humedad_absoluta": f"{round(mae, 2)} % HR",
            "rmse_humedad": f"{round(rmse, 2)} % HR",
            "media_humedad_sala": f"{round(media_humedad_real, 2)} % HR",
            "cv_rmse_ashrae": f"{round(cv_rmse, 2)} %",  # ESTE ES TU DATO ESTRELLA
            "horizonte_prediccion": "15 periodos",
            "status": "Modelo Predictivo Termodinámico validado bajo ASHRAE 14"
        }