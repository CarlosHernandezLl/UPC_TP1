import joblib
import pandas as pd
import matplotlib.pyplot as plt
import os

def analyze_hvac_model():
    model_path = os.path.join("app", "ml", "hvac_model.pkl")
    
    if not os.path.exists(model_path):
        print("Error: No se encuentra el archivo hvac_model.pkl")
        return

    # 1. Cargar el modelo
    model = joblib.load(model_path)
    
    # 2. Definir las variables en el orden exacto del entrenamiento
    features = [
        't_secador', 'h_secador', 't_uma', 'h_uma', 
        't_sala', 'h_sala', 't_ext', 'h_ext'
    ]
    
    # 3. Extraer la importancia de cada variable
    importances = model.feature_importances_
    
    # 4. Crear un DataFrame para visualizar mejor
    feature_importance = pd.DataFrame({
        'Variable': features,
        'Importancia (%)': importances * 100
    }).sort_values(by='Importancia (%)', ascending=False)

    print("\n--- IMPORTANCIA DE VARIABLES PARA LA POTENCIA ---")
    print(feature_importance)
    
    # 5. Guardar un gráfico (Opcional para tu informe de tesis)
    plt.figure(figsize=(10, 6))
    plt.barh(feature_importance['Variable'], feature_importance['Importancia (%)'], color='skyblue')
    plt.xlabel('Impacto en la Predicción (%)')
    plt.title('¿Qué variables mueven la potencia del HVAC?')
    plt.gca().invert_yaxis()
    plt.savefig('model_importance.png')
    print("\nGráfico guardado como 'model_importance.png'")

if __name__ == "__main__":
    analyze_hvac_model()