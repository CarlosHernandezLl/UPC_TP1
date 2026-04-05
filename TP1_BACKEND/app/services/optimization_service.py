import pandas as pd
import joblib
import os
import numpy as np
from app.schemas.optimization import OptimizationInput

class OptimizationService:
    def __init__(self):
        self.model_path = os.path.join("app", "ml", "hvac_model.pkl")
        self.feature_names = [
            "temp_secador", "hum_secador",
            "temp_uma", "hum_uma", 
            "temp_sala", "hum_sala",
            "temp_ext", "hum_ext"
        ]

    async def run_optimization(self, data: OptimizationInput):
        # 1. Cargar el modelo entrenado
        if not os.path.exists(self.model_path):
            return {"error": "Modelo no entrenado. No puedo optimizar."}
        
        model = joblib.load(self.model_path)

        # 2. Definir el "Espacio de Búsqueda" (Rangos Seguros Farmacéuticos)
        # Probamos t_uma de 20°C a 24°C y h_uma de 45% a 55%
        t_values = np.arange(20.0, 24.5, 0.5) 
        h_values = np.arange(45.0, 56.0, 1.0)

        mejor_potencia = data.potencia_actual
        mejor_t_uma = 22.0 # Fallback/Valor por defecto
        mejor_h_uma = 50.0
        encontro_ahorro = False

        # 3. El Bucle de Pensamiento (Simulación de escenarios)
        for t_test in t_values:
            for h_test in h_values:
                # Creamos el DataFrame para que el modelo "prediga" este escenario
                input_df = pd.DataFrame([[
                    data.temp_secador, data.hum_secador,
                    float(t_test), float(h_test),
                    data.temp_sala, data.hum_sala,
                    data.temp_ext, data.hum_ext
                ]], columns=self.feature_names)

                # El modelo estima cuánta potencia se gastaría con este setpoint
                pred_potencia = float(model.predict(input_df)[0])

                # Si este escenario gasta menos que el actual, lo guardamos
                if pred_potencia < mejor_potencia:
                    mejor_potencia = pred_potencia
                    mejor_t_uma = t_test
                    mejor_h_uma = h_test
                    encontro_ahorro = True

        # 4. Calcular el ahorro porcentual
        ahorro_relativo = data.potencia_actual - mejor_potencia
        porcentaje_ahorro = (ahorro_relativo / data.potencia_actual * 100) if data.potencia_actual > 0 else 0

        return {
            "setpoint_t_uma_sugerido": round(float(mejor_t_uma), 2),
            "setpoint_h_uma_sugerido": round(float(mejor_h_uma), 2),
            "potencia_estimada_nueva": round(mejor_potencia, 2),
            "ahorro_estimado_kw_o_pct": round(ahorro_relativo, 2),
            "porcentaje_mejora": f"{round(porcentaje_ahorro, 2)}%",
            "viabilidad_pharma": "DENTRO DE RANGO",
            "metodo": "Grid Search Optimization"
        }