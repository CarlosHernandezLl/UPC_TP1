# TP1_MACHINE/ai_service.py
import xgboost as xgb
import joblib
import pandas as pd
import numpy as np
import os
from ssd_service import SSDService # Importamos el filtro

class MLEngine:
    def __init__(self):
        self.model_path = "model.joblib"
        # Mismo orden que en tu Notebook
        self.features = ['potencia_secador', 'temp_ext', 'w_ext', 'temp_uma', 'w_uma', 'f20910p']
        
    def entrenar_modelo(self, datos_crudos_json):
        """
        Mapea a tu: entrenar_modelo_estacionario_masivo(df_oro)
        """
        df_raw = pd.DataFrame(datos_crudos_json)
        
        # 1. Llamamos al SSD Service para sacar la matriz de oro
        df_oro = SSDService.extraer_todos_los_minutos_estacionarios(df_raw)
        
        # 2. Vector de Monotonía (Tu diseño de Caja Gris)
        restricciones = (-1, 0, 1, -1, 1, 0)
        
        model = xgb.XGBRegressor(
            n_estimators=60, max_depth=3, learning_rate=0.05,
            monotone_constraints=restricciones, objective='reg:squarederror'
        )
        
        model.fit(df_oro[self.features], df_oro['w_sala'])
        
        # Guardamos el modelo
        joblib.dump({"model": model, "min_potencia": float(df_oro['potencia_secador'].min())}, self.model_path)
        return {"status": "success", "filas_usadas": len(df_oro)}

    def predecir_y_optimizar(self, datos_supervisor):
        """
        Mapea a tu: optimizar_consumo_granular(...) de la Celda 7
        """
        artifact = joblib.load(self.model_path)
        model = artifact["model"]
        
        p_actual = datos_supervisor['potencia_secador']
        t_sala = datos_supervisor['temp_sala']
        # Calculamos la presión de vapor de la sala (tu fórmula de Buck)
        es_sala = 6.1121 * np.exp((18.678 - t_sala / 234.5) * (t_sala / (257.14 + t_sala)))
        
        # TU BUCLE ITERATIVO DESCENDENTE EXACTO
        mejor_potencia = p_actual
        for p in np.arange(int(p_actual), int(artifact["min_potencia"]) - 1, -1):
            
            df_input = pd.DataFrame([[p, datos_supervisor['temp_ext'], datos_supervisor['w_ext'], 
                                      datos_supervisor['temp_uma'], datos_supervisor['w_uma'], 
                                      datos_supervisor['f20910p']]], columns=self.features)
            
            w_sala_pred = model.predict(df_input)[0]
            
            # Conversión psicrométrica inversa (Como en tu Celda 7)
            k = w_sala_pred / 622.0
            e_pred = (1013.50 * k) / (1.0 + k)
            hr_sala_pred = (e_pred / es_sala) * 100.0
            
            if hr_sala_pred <= (50.0 - 0.2): # Límite GMP con margen de seguridad
                mejor_potencia = float(p)
            else:
                break # Rompe el bucle gracias a las restricciones monótonas
                
        return {"potencia_recomendada": mejor_potencia, "ahorro_kw": p_actual - mejor_potencia}