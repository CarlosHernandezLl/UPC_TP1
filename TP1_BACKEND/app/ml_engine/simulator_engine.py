# app/ml_engine/simulator_engine.py
import xgboost as xgb
import pandas as pd
import numpy as np
import os
import json
import logging

logger = logging.getLogger(__name__)

class SimulatorEngine:
    def __init__(self):
        self.model = xgb.XGBRegressor()
        self.r2_score = 0.0
        self.mse = 0.0
        
        # Rutas dinámicas
        base_path = os.path.dirname(__file__)
        self.model_path = os.path.join(base_path, "saved_models", "xgboost_hvac_v1.json")
        self.metadata_path = os.path.join(base_path, "saved_models", "model_metadata.json")
        
        # 1. Cargar el modelo físico
        try:
            self.model.load_model(self.model_path)
            logger.info("✅ Modelo XGBoost de Gemelo Digital cargado en memoria RAM.")
        except Exception as e:
            logger.error(f"❌ No se pudo cargar el archivo del modelo: {e}")

        # 2. Cargar las métricas reales del entrenamiento (Sin hardcodeo)
        try:
            with open(self.metadata_path, 'r') as f:
                meta = json.load(f)
                self.r2_score = float(meta.get("r2_score", 0.0))
                self.mse = float(meta.get("mse", 0.0))
            logger.info(f"📊 Métricas reales vinculadas: R² = {self.r2_score}%")
        except Exception as e:
            logger.error(f"⚠️ No se pudo leer la metadata real del modelo: {e}")

    def _calcular_w(self, temp, hr, p=1013.25):
        """Calcula la Razón de Humedad Absoluta (w) usando Buck (1981)"""
        es = 6.1121 * np.exp((18.678 - temp / 234.5) * (temp / (257.14 + temp)))
        e = (hr / 100.0) * es
        return 1000.0 * (0.62197 * e / (p - e))

    def recomendar_potencia(self, temp_ext, hum_ext, temp_uma, hum_uma, setpoint_hr_sala):
        """Prueba las potencias y encuentra el mínimo error respecto al setpoint"""
        w_ext = float(hum_ext) if float(hum_ext) < 30.0 else self._calcular_w(temp_ext, hum_ext, p=1013.25)
        w_uma = float(hum_uma) if float(hum_uma) < 30.0 else self._calcular_w(temp_uma, hum_uma, p=1015.00)
        setpoint_w_sala = self._calcular_w(22.0, setpoint_hr_sala, p=1013.50)

        potencias_prueba = np.arange(10, 101, 1)
        total_escenarios = len(potencias_prueba)
        
        df_sim = pd.DataFrame({
            'potencia_secador': potencias_prueba,
            'temp_ext': np.full(total_escenarios, temp_ext),
            'w_ext': np.full(total_escenarios, w_ext),
            'temp_uma': np.full(total_escenarios, temp_uma),
            'w_uma': np.full(total_escenarios, w_uma),
            'presion_inyeccion': np.full(total_escenarios, 1015.00)
        })

        cols = ['potencia_secador', 'temp_ext', 'w_ext', 'temp_uma', 'w_uma', 'presion_inyeccion']
        predicciones_w_sala = self.model.predict(df_sim[cols])

        errores = np.abs(predicciones_w_sala - setpoint_w_sala)
        idx_optimo = np.argmin(errores)
        
        potencia_ideal = float(potencias_prueba[idx_optimo])
        w_sala_logrado = float(predicciones_w_sala[idx_optimo])

        limite_gmp_w = self._calcular_w(22.0, 55.0)
        alerta_gmp = True if (setpoint_hr_sala > 55.0) or (w_sala_logrado > limite_gmp_w) else False

        return potencia_ideal, alerta_gmp