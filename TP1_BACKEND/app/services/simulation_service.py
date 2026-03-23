import pandas as pd
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

    count = 0
    for _, row in df_clean.iterrows():
        
        #Timestamp PLC
        ts_plc = pd.to_datetime(row["Timestamp_PLC"])
        
        #Timestamp datalogger (Solo Hora)
        try:
            hora_dl = pd.to_datetime(row["Timestamp_DL"]).time()
            ts_dl = datetime.combine(ts_plc.date(), hora_dl)
            
            #Ajuste por proximidad: si difiere demasiado, usar PLC
            if abs((ts_dl- ts_plc).total_seconds()) > 30:
                ts_dl = ts_plc
        except Exception:
            ts_dl = ts_plc
        
        
        # if isinstance(ts_dl, str) or pd.isna(ts_dl):
        #     #Convertir a hora
        #     try:
        #         hora_dl = pd.to_datetime(ts_dl).time()
        #         ts_dl = datetime.combine(ts_plc.date(), hora_dl)
        #     except Exception:
        #         ts_dl = ts_plc  
        #         # fallback: usar timestamp del PLC

        
        
        # Insertar en tabla PLC
        plc_entry = RawPlcData(
            timestamp = row["Timestamp_PLC"],
            temp_secador = row["T secador"],
            hum_secador = row["H secador"],
            temp_uma = row["T uma"],
            hum_uma = row["H uma"],
            potencia = row["Potencia de secador %"]
        )
        
        # Insertar en tabla Datalogger
        dl_entry = RawDataloggerData(
            timestamp= ts_dl,
            temp_sala=row["T sala"],
            hum_sala=row["H sala"]
        )
        
        # Insertar en tabla Clima (Simulando que el clima actual se aplica a ese registro)
        weather_entry = RawWeatherData(
            timestamp= ts_plc,
            temp_ext=weather["temperatura_exterior"],
            hum_ext=weather["humedad_exterior"]
        )
        
        db.add_all([plc_entry,dl_entry,weather_entry])
        
    db.commit()
    print("Carga inicial completada")