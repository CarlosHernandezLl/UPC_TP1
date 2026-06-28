import os
import json
import logging
from datetime import datetime
import xgboost as xgb
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# 🎯 IMPORTS CIENTÍFICOS: Alineados exactamente a la metodología de tu cuaderno
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import r2_score, mean_squared_error
from app.models.hvac_model import HvacHistoricalData

logger = logging.getLogger(__name__)

class MLTrainingService:
    def __init__(self, db: Session, simulator_engine):
        self.db = db
        self.simulator_engine = simulator_engine

    def _calcular_umbral_optimo_estadistico(self, df: pd.DataFrame, percentil=0.90) -> float:
        """Analiza la derivada higrométrica en la grilla continua de la BD"""
        diff_w = df['w_sala'].diff().abs().dropna()
        smooth_diff = diff_w.rolling(window=5, min_periods=1).mean()
        return float(smooth_diff.quantile(percentil))

    def _extraer_minutos_estacionarios(self, df_raw: pd.DataFrame, patience=10) -> pd.DataFrame:
        """Algoritmo SSD ejecutado en RAM sobre la serie de tiempo continua"""
        df = df_raw.copy().sort_values('ts').reset_index(drop=True)
        df['diff_w'] = df['w_sala'].diff().abs()
        df['cambio_escalon'] = (df['potencia_secador'] != df['potencia_secador'].shift()).cumsum()

        umbral_estabilidad = self._calcular_umbral_optimo_estadistico(df, percentil=0.90)
        lista_df_estables = []

        for _, grupo in df.groupby('cambio_escalon'):
            if len(grupo) < 20: 
                continue

            data_escalon = grupo.copy()
            data_escalon['smooth_diff'] = data_escalon['diff_w'].rolling(window=5, min_periods=1).mean()
            estabilidad = data_escalon['smooth_diff'] < umbral_estabilidad

            idx_estabilizacion_real = None
            conteo = 0

            for idx in data_escalon.index:
                if estabilidad.loc[idx]:
                    conteo += 1
                else:
                    conteo = 0

                if conteo >= patience:
                    idx_estabilizacion_real = idx
                    break

            if idx_estabilizacion_real is not None:
                datos_post_estabilizacion = data_escalon.loc[idx_estabilizacion_real:]
                data_stable = datos_post_estabilizacion[datos_post_estabilizacion['smooth_diff'] < umbral_estabilidad].copy()
                lista_df_estables.append(data_stable)

        if not lista_df_estables:
            return pd.DataFrame()

        return pd.concat(lista_df_estables).reset_index(drop=True)

    def ejecutar_reentrenamiento_masivo(self) -> dict:
        """Pipeline MLOps que extrae la data, la purifica en RAM y actualiza los pesos"""
        # 1. Extraer la serie temporal continua desde Supabase
        db_records = self.db.query(HvacHistoricalData).order_by(HvacHistoricalData.timestamp.asc()).all()
        
        if not db_records:
            return {"status": "error", "message": "La base de datos de telemetría está vacía."}
            
        # 🎯 CORRECCIÓN: Incorporamos 'ts' para el SSD y 'presion_inyeccion' exigida por el modelo de tu tesis
        df_raw = pd.DataFrame([{
            'ts': r.timestamp,
            'potencia_secador': r.potencia_secador,
            'temp_ext': r.temp_ext,
            'w_ext': r.w_ext,
            'temp_uma': r.temp_uma,
            'w_uma': r.w_uma,
            'presion_inyeccion': getattr(r, 'presion_inyeccion', 1015.0), # Resiliente si la migración es reciente
            'w_sala': r.w_sala
        } for r in db_records])

        # 2. FILTRADO EN RAM: Aplicamos el SSD calculando derivadas perfectas
        df_oro = self._extraer_minutos_estacionarios(df_raw)

        if df_oro.empty:
            return {"status": "error", "message": "No se encontraron suficientes ventanas de equilibrio térmico."}

        # 3. Preparación de Matrices (Hold-out por Grupos idéntico a tu Jupyter)
        # 🎯 CORRECCIÓN: Inclusión de la 6ta variable física crítica del ducto
        columnas_x = ['potencia_secador', 'temp_ext', 'w_ext', 'temp_uma', 'w_uma', 'presion_inyeccion'] 
        
        X = df_oro[columnas_x]
        y = df_oro['w_sala']
        grupos = df_oro['cambio_escalon']

        # Ejecutamos la división científica de datos (80% Entrenamiento / 20% Validación)
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        train_idx, test_idx = next(gss.split(X, y, groups=grupos))

        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

        # 4. INJECCIÓN DE CONSTRAINTS MONÓTONOS (6 elementos para reflejar la física del proceso)
        restricciones = (-1, 0, 1, -1, 1, 0) 
        
        model = xgb.XGBRegressor(
            n_estimators=60,
            max_depth=3,
            learning_rate=0.05,
            monotone_constraints=restricciones,
            random_state=42
        )
        
        # 5. Ajuste del modelo matemático sobre el set de entrenamiento aislado
        model.fit(X_train, y_train)

        # 6. Evaluación de calidad real sobre el Hold-out set
        preds = model.predict(X_test)
        r2_real = r2_score(y_test, preds)
        mse_real = mean_squared_error(y_test, preds)

        # Definición de rutas absolutas basadas en la ubicación de este archivo de servicio
        base_path = os.path.dirname(__file__)
        model_dir = os.path.abspath(os.path.join(base_path, "..", "ml_engine", "saved_models"))
        os.makedirs(model_dir, exist_ok=True) # Crea la carpeta si no existiera
        
        path_modelo = os.path.join(model_dir, "xgboost_hvac_v1.json")
        path_metadata = os.path.join(model_dir, "model_metadata.json")

        model.save_model(path_modelo)

        metadata_modelo = {
            "r2_score": round(float(r2_real) * 100, 2),
            "mse": round(float(mse_real), 6),
            "version": datetime.now().strftime("1.%m.%d"),
            "last_trained": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(path_metadata, "w") as f:
            json.dump(metadata_modelo, f, indent=4)

        self.simulator_engine.reload_model_in_memory()

        return {
            "status": "success",
            "message": f"Algoritmo validado y desplegado en caliente. R²: {metadata_modelo['r2_score']}%, Registros Oro: {len(df_oro)}."
        }