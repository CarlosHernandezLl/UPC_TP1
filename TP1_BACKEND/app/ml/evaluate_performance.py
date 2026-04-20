import pandas as pd
import numpy as np
import joblib
import os
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def calculate_metrics():
    # 1. Cargar el Modelo y los Datos
    model_path = os.path.join("app", "ml", "hvac_model.pkl")
    data_path = os.path.join("data", "prueba.xlsx") # O el nombre de tu archivo actual

    if not os.path.exists(model_path):
        print("Error: No se encuentra el modelo entrenado.")
        return

    model = joblib.load(model_path)
    
    # Leemos y mapeamos como en el simulation_service
    df = pd.read_excel(data_path, skiprows=1, engine='openpyxl')
    
    mapping = {
        'f20914t': 'temp_secador', 'f20914h': 'hum_secador',
        'f20911t': 'temp_uma', 'f20911h': 'hum_uma',
        'f209potsecador': 'potencia',
        'temp_ext': 'temp_ext', 'hum_ext': 'hum_ext',
        'temperatura': 'temp_sala', 'Humedad': 'hum_sala'
    }
    df = df.rename(columns=mapping)
    df = df.dropna(subset=['potencia', 'temp_secador', 'temp_sala'])

    # 2. Métricas de Precisión (Accuracy)
    features = ["temp_secador", "hum_secador", "temp_uma", "hum_uma", "temp_sala", "hum_sala", "temp_ext", "hum_ext"]
    X = df[features]
    y_real = df['potencia']
    y_pred = model.predict(X)

    mae = mean_absolute_error(y_real, y_pred)
    rmse = np.sqrt(mean_squared_error(y_real, y_pred))
    r2 = r2_score(y_real, y_pred)

    # 3. Métricas de Optimización (Simulación de Ahorro Masivo)
    # Vamos a ver cuánto se ahorraría en promedio si el optimizador hubiera actuado
    potencias_optimizadas = []
    
    print("Simulando optimización en todo el dataset (esto puede tardar)...")
    
    # Rango de búsqueda para la simulación
    t_values = np.arange(20.0, 24.5, 0.5)
    
    for _, row in df.sample(min(100, len(df))).iterrows(): # Usamos una muestra para rapidez
        best_p = row['potencia']
        for t_test in t_values:
            test_df = pd.DataFrame([[
                row['temp_secador'], row['hum_secador'], t_test, row['hum_uma'],
                row['temp_sala'], row['hum_sala'], row['temp_ext'], row['hum_ext'] if 'hum_ext' in row else 60.0
            ]], columns=features)
            p_sim = model.predict(test_df)[0]
            if p_sim < best_p:
                best_p = p_sim
        potencias_optimizadas.append(best_p)

    avg_saving = y_real.mean() - np.mean(potencias_optimizadas)
    pct_saving = (avg_saving / y_real.mean()) * 100

    # 4. Reporte Final para la Tesis
    print("\n" + "="*40)
    print("   MÉTRICAS DE RENDIMIENTO DEL MODELO")
    print("="*40)
    print(f"1. Precisión (R²):           {r2:.4f}")
    print(f"2. Error Medio (MAE):        {mae:.2f} %")
    print(f"3. Error Cuadrático (RMSE):  {rmse:.2f} %")
    print("-"*40)
    print("   MÉTRICAS DE IMPACTO ENERGÉTICO")
    print("-"*40)
    print(f"4. Potencia Promedio Actual: {y_real.mean():.2f} %")
    print(f"5. Ahorro Promedio Est.:     {avg_saving:.2f} puntos")
    print(f"6. MEJORA DE EFICIENCIA:     {pct_saving:.2f} %")
    print("="*40)

if __name__ == "__main__":
    calculate_metrics()