import pandas as pd
import numpy as np
import os
from sqlalchemy.orm import Session
from app.repositories.hvac_repository import HvacRepository
from app.schemas.hvac import HvacReadingCreate
from app.services.weather_service import get_external_weather
import logging
from app.models.raw_data import RawPlcData, RawDataloggerData, RawWeatherData



logger = logging.getLogger(__name__)

async def load_excel_data_to_db(db: Session):
    # Localización dinámica del archivo
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FILE_PATH = os.path.join(BASE_DIR, "data", "data.xlsx")

    if not os.path.exists(FILE_PATH):
        print(f"Error: No se encontró el archivo en {FILE_PATH}")
        return None

    # Leemos el Excel. 
    # 'skiprows=1' si es que la primera fila son títulos generales y la segunda los nombres de columnas
    df = pd.read_excel(FILE_PATH, skiprows= 1, engine='openpyxl')
    #print(df.head())
    #print(df.columns.tolist())
    
    plc_cols = ['T secador','H secador', 'T uma', 'H uma', 'Potencia de secador %']
    # plc_time_col = df.columns[5]
    datalogger_cols = ['H sala', 'T sala']

    #Limpieza: eliminar filas con timestamps nulos
    df = df.dropna(subset=["Timestamp_PLC", "Timestamp_DL"]).copy()
    
    #Eliminar filas con valores nulos en PLC
    df_clean = df.dropna(subset= plc_cols).copy()
    
    #Rellenar valores faltantes en datalogger
    df_clean[datalogger_cols] = df_clean[datalogger_cols].ffill()
    
    hvac_repo = HvacRepository(db)
    
    # Obtenemos clima actual para completar las 8 variables
    weather = await get_external_weather()
    temp_ext = weather["temperatura_exterior"] if weather else 20.0
    hum_ext = weather["humedad_exterior"] if weather else 60.0

    ## AQUI VA
    total_rows = len(df_clean)
    filas_por_dia = 144
    
    count = 0
    for i, (index, row) in enumerate(df_clean.iterrows()):
        # --- NUEVA LÓGICA DE CLIMA VARIABLE ---
        # Calculamos la fase del día (de 0 a 1)
        fase = (i % filas_por_dia) / filas_por_dia
        t_ext_sim = float(22 + 5 * np.sin(2 * np.pi * (fase - 0.25))) # <-- Convertir aquí
        h_ext_sim = float(70 - 15 * np.sin(2 * np.pi * (fase - 0.25)))

        # Timestamp PLC (Tu lógica)
        ts_plc = pd.to_datetime(row["Timestamp_PLC"])
        
        # Timestamp datalogger (Tu lógica)
        try:
            hora_dl = pd.to_datetime(row["Timestamp_DL"]).time()
            ts_dl = datetime.combine(ts_plc.date(), hora_dl)
            if abs((ts_dl - ts_plc).total_seconds()) > 30:
                ts_dl = ts_plc
        except Exception:
            ts_dl = ts_plc

        # 3. Inserción en las 3 tablas RAW
        plc_entry = RawPlcData(
            timestamp=ts_plc,
            temp_secador=row["T secador"],
            hum_secador=row["H secador"],
            temp_uma=row["T uma"],
            hum_uma=row["H uma"],
            potencia=row["Potencia de secador %"]
        )
        
        dl_entry = RawDataloggerData(
            timestamp=ts_dl,
            temp_sala=row["T sala"],
            hum_sala=row["H sala"]
        )
        
        weather_entry = RawWeatherData(
            timestamp=ts_plc,
            temp_ext=round(t_ext_sim, 2), # Usamos el valor simulado
            hum_ext=round(h_ext_sim, 2)  # Usamos el valor simulado
        )
        
        db.add_all([plc_entry, dl_entry, weather_entry])
        count += 1

        # Commit parcial cada 100 registros para eficiencia
        if count % 100 == 0:
            db.commit()
        
    db.commit()
    print(f"Carga inicial completada: {count} registros con clima dinámico.")
    return count