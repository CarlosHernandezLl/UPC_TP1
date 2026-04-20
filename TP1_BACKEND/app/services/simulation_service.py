import pandas as pd
import numpy as np
import os
from sqlalchemy.orm import Session
from app.repositories.hvac_repository import HvacRepository
from app.schemas.hvac import HvacReadingCreate
from app.services.weather_service import get_external_weather
import logging
from app.models.raw_data import RawPlcData, RawDataloggerData, RawWeatherData
from sqlalchemy import text

logger = logging.getLogger(__name__)

async def load_excel_data_to_db(db: Session):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    FILE_PATH = os.path.join(BASE_DIR, "data", "dataset_19_04_2026.xlsx")

    if not os.path.exists(FILE_PATH):
        logger.error(f"Error: No se encontró el archivo en {FILE_PATH}")
        return None
    
    try:
        db.execute(text("TRUNCATE TABLE raw_plc_data, raw_datalogger_data, raw_weather_data CASCADE"))
        db.commit()
        print("Bases de datos limpiadas para nueva simulación.")
    except Exception as e:
        db.rollback()
        print(f"Aviso: No se pudo limpiar las tablas: {e}")
    
    # skiprows=1 si la primera fila son títulos y la segunda los nombres de columnas
    # df = pd.read_excel(FILE_PATH, skiprows=1, engine='openpyxl')
    df = pd.read_excel(FILE_PATH, engine='openpyxl')
    
    column_mapping = {
        'f20914t': 'T secador',
        'f20914h': 'H secador',
        'f20911t': 'T uma',
        'f20911h': 'H uma',
        'f209potsecador': 'Potencia de secador %',
        'fecha': 'Timestamp_PLC',
        
        #Datos de Clima (API)
        'timestamp': 'Timestamp_API',
        'temp_ext': 't_ext',
        'hum_ext': 'h_ext',
        
        #Datos del Datalogger (USB)
        'Fecha': 'DL_Fecha',
        'Hora': 'DL_Hora',
        'Temperatura': 'T sala',
        'Humedad': 'H sala',
    }
    
    df = df.rename(columns=column_mapping)
    
    df['Timestamp_PLC'] = pd.to_datetime(df['Timestamp_PLC'])
    df['Timestamp_API'] = pd.to_datetime(df['Timestamp_API'])
    
    #B. Unificar Datalogger: Combinar Fecha + Hora en un solo Timestamp
    #Convertimos a string, concatenamos y luego a datetime
    df['Timestamp_DL'] = pd.to_datetime(
        df['DL_Fecha'].astype(str) + ' ' + df['DL_Hora'].astype(str)
    )
    
    # df = df.dropna(subset=["Timestamp_PLC", "T secador", "T sala"]).copy()
    df = df.dropna(subset=["Timestamp_PLC", "Timestamp_DL", "Timestamp_API"]).copy()
    df['Timestamp_PLC'] = pd.to_datetime(df['Timestamp_PLC'])
    
    # El ffill es clave para el Datalogger (USB) si tiene menos muestras que el PLC
    #df['T sala'] = df['T sala'].ffill()
    #df['H sala'] = df['H sala'].ffill()
    
    count = 0
    batch_size = 100
    
    try:
        for index, row in df.iterrows():
            # ts_actual = row["Timestamp_PLC"]

            # 1. Objeto para Tabla PLC (Datos de control)
            plc_entry = RawPlcData(
                timestamp= row["Timestamp_PLC"],
                temp_secador=float(row["T secador"]),
                hum_secador=float(row["H secador"]),
                temp_uma=float(row["T uma"]),
                hum_uma=float(row["H uma"]),
                potencia=float(row["Potencia de secador %"])
            )
            
            # 2. Objeto para Tabla Datalogger (La "verdad" del USB)
            dl_entry = RawDataloggerData(
                timestamp= row["Timestamp_DL"],
                temp_sala=float(row["T sala"]),
                hum_sala=float(row["H sala"])
            )
            
            # 3. Objeto para Tabla Clima (Datos de Lima)
            weather_entry = RawWeatherData(
                timestamp= row["Timestamp_API"],
                temp_ext=float(row["t_ext"]),
                hum_ext=float(row["h_ext"])
            )
            
            db.add_all([plc_entry, dl_entry, weather_entry])
            count += 1
            
            # Commit parcial cada 100 registros para no saturar la memoria
            if count % batch_size == 0:
                db.commit()
        
        # --- FUERA DEL BUCLE ---
        db.commit() # Guardamos el resto
        print(f"✅ Carga completada: {count} registros procesados con éxito.")
        return count

    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error durante la carga: {e}")
        return None