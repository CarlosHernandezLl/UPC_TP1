# app/services/data_service.py
from sqlalchemy.orm import Session
import pandas as pd
from app.models.hvac_model import HvacHistoricalData
from fastapi import HTTPException
import numpy as np
import io


class DataService:
    def __init__(self, db: Session):
        self.db = db
        
    def _calculate_psychrometrics(self, temp, hr):
        try:
            if pd.isna(temp) or pd.isna(hr):
                return 0.0
        
            # Forzamos la conversión para detectar si hay texto
            t = float(temp)
            h = float(hr)

            es = 6.112 * np.exp((17.67 * t) / (t + 243.5))
            ev = es * (h / 100)
            p_atm = 1013.25
            w = 0.622 * (ev / (p_atm - ev))
            return round(w, 6)
        
        except Exception as e:
            # Esto te dirá exactamente qué valores causaron el fallo
            print(f"❌ Error calculando 'w' con Temp: {temp} (Tipo: {type(temp)}) y HR: {hr} (Tipo: {type(hr)})")
            print(f"Detalle: {e}")
            return 0.0 # O lanza el error de nuevo tras el print

    def _clean_sensor_noise(self, df: pd.DataFrame):
        """Elimina valores físicamente imposibles en sensores HVAC."""
        if 'hum_sala' in df.columns:
            df = df[(df['hum_sala'] >= 0) & (df['hum_sala'] <= 100)]
        if 'temp_sala' in df.columns:
            df = df[(df['temp_sala'] >= -10) & (df['temp_sala'] <= 60)]
        return df

    async def upload_and_sync(self, file_plc, file_logger, file_externo, start_date: str, end_date: str):
        try:
            # 1. Leer contenido de los UploadFiles           
            plc_bytes = await file_plc.read()
            logger_bytes = await file_logger.read()
            externo_bytes = await file_externo.read()
            
            filename = file_logger.filename.lower()
            
            # 2. Convertir a buffers para Pandas
            df_plc = pd.read_csv(io.BytesIO(plc_bytes), sep=',')
            df_externo = pd.read_csv(io.BytesIO(externo_bytes), sep=',')
            
            if filename.endswith(".csv") or filename.endswith(".xls"):
                # Tratarlo como CSV
                df_logger = pd.read_csv(io.BytesIO(logger_bytes), sep="\t", skiprows=20, encoding="latin1")
            else:
                # Tratarlo como Excel real
                df_logger = pd.read_excel(io.BytesIO(logger_bytes), skiprows=20, engine="openpyxl")
            
            # Normalizar nombres de columnas
            df_plc.columns = df_plc.columns.str.strip()
            df_logger.columns = df_logger.columns.str.strip()
            df_externo.columns = df_externo.columns.str.strip()
            
            # 2. ESTANDARIZACIÓN DE TIEMPOS
            df_plc['ts'] = pd.to_datetime(df_plc['fecha'], errors="coerce")
            df_externo['ts'] = pd.to_datetime(df_externo['timestamp'], errors="coerce")
            df_logger['ts'] = pd.to_datetime(df_logger['Fecha'] + ' ' + df_logger['Hora'], errors="coerce")

            
            # 3. APLICAR PUNTO DE CORTE INDIVIDUAL (Limpieza temprana)
            sd, ed = pd.to_datetime(start_date), pd.to_datetime(end_date)
            if sd > ed:
                sd, ed = ed, sd  # intercambia si están invertidas
            print("Rango solicitado:", sd, ed)
        
            df_plc = df_plc[(df_plc['ts'] >= sd) & (df_plc['ts'] <= ed)]
            df_logger = df_logger[(df_logger['ts'] >= sd) & (df_logger['ts'] <= ed)]
            df_externo = df_externo[(df_externo['ts'] >= sd) & (df_externo['ts'] <= ed)]

            if df_plc.empty or df_logger.empty or df_externo.empty:
                raise ValueError("Uno de los archivos no tiene datos en el rango seleccionado.")
            
            
            # 4. SINCRONIZACIÓN (Merge Asof)
            # Ordenar es obligatorio para merge_asof
            df_plc = df_plc.sort_values('ts')
            df_logger = df_logger.sort_values('ts')
            df_externo = df_externo.sort_values('ts')
            
            print("PLC ts:", df_plc['ts'].dropna().min(), df_plc['ts'].dropna().max())
            print("Logger ts:", df_logger['ts'].dropna().min(), df_logger['ts'].dropna().max())
            print("Externo ts:", df_externo['ts'].dropna().min(), df_externo['ts'].dropna().max())
            print("Rango solicitado:", sd, ed)


            merged = pd.merge_asof(df_plc, df_externo, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            merged = pd.merge_asof(merged, df_logger, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            
            keep_cols = ['ts','f20911t','f20911h','f20910p','f209potsecador',
                         'temp_ext','hum_ext','Temperatura','Humedad']
            
            merged = merged[keep_cols]
            
            for col in keep_cols:
                if col != 'ts':
                    merged[col] = pd.to_numeric(merged[col], errors='coerce')
                    
            start_common = max(df_plc['ts'].min(), df_logger['ts'].min(), df_externo['ts'].min())
            end_common = min(df_plc['ts'].max(), df_logger['ts'].max(), df_externo['ts'].max())
            merged = merged[(merged['ts'] >= start_common) & (merged['ts'] <= end_common)]            
            

            # 5. NORMALIZACIÓN A 1 MINUTO (Upsampling e Interpolación)
            # Si ya está a 1 min, esto solo llena huecos vacíos si existen.
            merged.set_index('ts', inplace=True)
            merged = merged.resample('1min').interpolate(method='linear')
            merged.reset_index(inplace=True)
            
            
            # 6. CÁLCULO DE VARIABLES FÍSICAS
            # Mapeo: PLC(f20911t=temp_uma, f20911h=hum_uma), LOG(Temperatura, Humedad), EXT(temp_ext, hum_ext)
            merged['w_ext'] = merged.apply(lambda x: self._calculate_psychrometrics(x['temp_ext'], x['hum_ext']), axis=1)
            merged['w_uma'] = merged.apply(lambda x: self._calculate_psychrometrics(x['f20911t'], x['f20911h']), axis=1)
            merged['w_sala'] = merged.apply(lambda x: self._calculate_psychrometrics(x['Temperatura'], x['Humedad']), axis=1)
            
            merged = merged.fillna(0.0)
            
            print("Columnas finales:", merged.columns)
            print("Tipos de datos:", merged.dtypes)
            print("Primeras filas:\n", merged.head(10))
            print("Valores nulos por columna:\n", merged.isna().sum())


            # 7. PERSISTENCIA EN BASE DE DATOS
            return self._save_records(merged)

        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=400, detail=f"Error en pipeline de datos: {str(e)}")

    
    def _save_records(self, df: pd.DataFrame):
        records = []
        for _, row in df.iterrows():
            record = HvacHistoricalData(
                timestamp=row['ts'],
                temp_ext=row['temp_ext'],
                w_ext=row.get('w_ext'),
                temp_uma=row['f20911t'], # Según tus headers
                w_uma=row.get('w_uma'),
                potencia_secador=row['f209potsecador'],
                temp_sala=row['Temperatura'],
                hum_sala=row['Humedad']
            )
            records.append(record)
        
        self.db.bulk_save_objects(records)
        self.db.commit()
        return {"message": f"{len(records)} registros insertados exitosamente."}