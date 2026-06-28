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
        
        base_path = os.path.dirname(__file__)
        self.model_path = os.path.join(base_path, "saved_models", "xgboost_hvac_v1.json")
        self.metadata_path = os.path.join(base_path, "saved_models", "model_metadata.json")
        self.reload_model_in_memory()
    
    def reload_model_in_memory(self):
        """🎯 HOT RELOADING: Carga o actualiza los pesos en RAM al re-entrenar"""
        try:
            if os.path.exists(self.model_path):
                self.model.load_model(self.model_path)
                logger.info("✅ [MLOps] Pesos del regresor XGBoost cargados/actualizados en RAM.")
            else:
                logger.warning("⚠️ No se encontró archivo del modelo físico (.json). Esperando inicialización.")
        except Exception as e:
            logger.error(f"❌ Error crítico al montar el archivo del modelo en memoria: {e}")

        try:
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    meta = json.load(f)
                    self.r2_score = float(meta.get("r2_score", 0.0))
                    self.mse = float(meta.get("mse", 0.0))
                logger.info(f"📊 [MLOps] Métricas actualizadas en caliente: R² = {self.r2_score}%")
        except Exception as e:
            logger.error(f"⚠️ No se pudo leer la metadata del modelo: {e}")
    
    def _calcular_w(self, temp, hr, p=1013.25):
        """Calcula la Razón de Humedad Absoluta (w) usando la formulación de Buck (1981)"""
        t = float(temp)
        rh = float(hr)
        es = 6.1121 * np.exp((18.678 - t / 234.5) * (t / (257.14 + t)))
        e = (rh / 100.0) * es
        
        return 1000.0 * (0.622 * e / (p - e))


    def recomendar_potencia(self, temp_ext, hum_ext, temp_uma, hum_uma, setpoint_hr_sala, 
                            min_hum_limit: float = 40.0, max_hum_limit: float = 55.0, temp_diseno_sala: float = 22.0):
        """
        Prueba de forma iterativa el espectro de potencias del PLC para hallar la óptima
        🎯 RANGO PARAMETRIZABLE: Evalúa tanto el límite inferior como el superior dinámicamente.
        """
        if not hasattr(self.model, "get_booster") or (hasattr(self.model, "feature_importances_") and len(self.model.feature_importances_) == 0):
            logger.error("Inferencia detenida: El modelo matemático no ha sido inicializado con un entrenamiento previo.")
            return 50.0, False 

        # 1. Cálculos psicrométricos de las condiciones reales
        w_ext = self._calcular_w(temp_ext, hum_ext, p=1013.25)
        w_uma = self._calcular_w(temp_uma, hum_uma, p=1015.00)
        setpoint_w_sala = self._calcular_w(temp_diseno_sala, setpoint_hr_sala, p=1013.50)

        # 2. Vector de simulación masiva (Modulación del variador del secador: 10% a 100%)
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

        # 3. Minimización del error absoluto respecto al setpoint objetivo
        errores = np.abs(predicciones_w_sala - setpoint_w_sala)
        idx_optimo = np.argmin(errores)
        
        potencia_ideal = float(potencias_prueba[idx_optimo])
        w_sala_logrado = float(predicciones_w_sala[idx_optimo])

        # 🎯 4. BARRERA DE BIENESTAR DE PRODUCTO (Rango Higrométrico GxP)
        limite_gmp_w_max = self._calcular_w(temp_diseno_sala, max_hum_limit)
        limite_gmp_w_min = self._calcular_w(temp_diseno_sala, min_hum_limit)
        
        # Alerta se dispara si el setpoint digitado está fuera de rango O si la predicción final viola los límites
        alerta_gmp = bool(
            (setpoint_hr_sala > max_hum_limit) or 
            (setpoint_hr_sala < min_hum_limit) or 
            (w_sala_logrado > limite_gmp_w_max) or 
            (w_sala_logrado < limite_gmp_w_min)
        )

        return potencia_ideal, alerta_gmp
    
    """
    def recomendar_potencia(self, temp_ext, hum_ext, temp_uma, hum_uma, setpoint_hr_sala):
        
        if not hasattr(self.model, "get_booster") or (blue_model_failed := (len(self.model.feature_importances_ if hasattr(self.model, "feature_importances_") else []) == 0)):
            logger.error("Inferencia detenida: El modelo matemático no ha sido inicializado con un entrenamiento previo.")
            return 50.0, False

        w_ext = self._calcular_w(temp_ext, hum_ext, p=1013.25)
        w_uma = self._calcular_w(temp_uma, hum_uma, p=1015.00)
        setpoint_w_sala = self._calcular_w(22.0, setpoint_hr_sala, p=1013.50)

        # Vector de simulación (Espectro de modulación del variador del secador: 10% a 100%)
        potencias_prueba = np.arange(10, 101, 1)
        total_escenarios = len(potencias_prueba)
        
        df_sim = pd.DataFrame({
            'potencia_secador': potencias_prueba,
            'temp_ext': np.full(total_escenarios, temp_ext),
            'w_ext': np.full(total_escenarios, w_ext),
            'temp_uma': np.full(total_escenarios, temp_uma),
            'w_uma': np.full(total_escenarios, w_uma),
            'presion_inyeccion': np.full(total_escenarios, 1015.00) # Presión absoluta estándar del ducto
        })

        cols = ['potencia_secador', 'temp_ext', 'w_ext', 'temp_uma', 'w_uma', 'presion_inyeccion']
        predicciones_w_sala = self.model.predict(df_sim[cols])

        # Minimización del error absoluto respecto al setpoint higrométrico deseado
        errores = np.abs(predicciones_w_sala - setpoint_w_sala)
        idx_optimo = np.argmin(errores)
        
        potencia_ideal = float(potencias_prueba[idx_optimo])
        w_sala_logrado = float(predicciones_w_sala[idx_optimo])

        limite_gmp_w = self._calcular_w(22.0, 55.0)
        alerta_gmp = True if (setpoint_hr_sala > 55.0) or (w_sala_logrado > limite_gmp_w) else False

        return potencia_ideal, alerta_gmp
    """