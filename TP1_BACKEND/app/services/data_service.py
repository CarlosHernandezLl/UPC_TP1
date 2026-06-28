from datetime import datetime
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
import io
import logging
from fastapi import HTTPException
from app.models.hvac_model import DataIngestionLog, HvacHistoricalData

logger = logging.getLogger(__name__)

class DataService:
    def __init__(self, db: Session):
        self.db = db
        
    def _calculate_psychrometrics(self, temp, hr, p_absolute):
        """
        Calcula la razón de humedad absoluta (W, g/kg) utilizando la formulación 
        empírica exacta de Buck (1981) alineada al manuscrito y al diseño experimental.
        """
        try:
            if pd.isna(temp) or pd.isna(hr) or pd.isna(p_absolute):
                return 0.0
        
            t = float(temp)
            rh = float(hr)
            p = float(p_absolute)

            # Ecuación de Buck (1981) original del modelo matemático
            es = 6.1121 * np.exp((18.678 - t / 234.5) * (t / (257.14 + t)))
            e = (rh / 100.0) * es
            
            # Constante molecular precisa (epsilon = 0.62197)
            w = 1000.0 * (0.62197 * e / (p - e))
            return round(w, 6)
        
        except Exception as err:
            logger.error(f"❌ Error psicrométrico - Temp: {temp}, HR: {hr}, P: {p_absolute}. Detalle: {err}")
            return 0.0

    def _clean_sensor_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Elimina valores físicamente imposibles para evitar heterocedasticidad y sesgos."""
        if 'Humedad' in df.columns:
            df = df[(df['Humedad'] >= 0) & (df['Humedad'] <= 100)]
        if 'Temperatura' in df.columns:
            df = df[(df['Temperatura'] >= -10) & (df['Temperatura'] <= 60)]
        return df


    # =================================================================
    # PIPELINE PRINCIPAL DE INGESTA
    # =================================================================
    async def upload_and_sync(self, file_plc, file_logger, file_externo, start_date: str = None, end_date: str = None) -> dict:
        try:
            # 1. Lectura asíncrona de los flujos binarios
            plc_bytes = await file_plc.read()
            logger_bytes = await file_logger.read()
            externo_bytes = await file_externo.read()
            
            # 2. Conversión a DataFrames
            df_plc = pd.read_csv(io.BytesIO(plc_bytes), sep=None, engine='python', encoding='utf-8')
            df_externo = pd.read_csv(io.BytesIO(externo_bytes), sep=None, engine='python', encoding='utf-8')
            
            filename_log = file_logger.filename.lower()
            if filename_log.endswith((".csv", ".txt", ".xls")):
                df_logger = pd.read_csv(io.BytesIO(logger_bytes), sep="\t", skiprows=20, encoding="latin1")
                if not df_logger.empty:
                    df_logger = df_logger.drop([0, 1, 2]).reset_index(drop=True)
            else:
                df_logger = pd.read_excel(io.BytesIO(logger_bytes), skiprows=20, engine="openpyxl")
                            
            for df_node in [df_plc, df_logger, df_externo]:
                df_node.columns = df_node.columns.str.strip()
            
            # 3. Estandarización de Timestamps
            df_plc['ts'] = pd.to_datetime(df_plc['fecha'], dayfirst=True, errors="coerce")
            df_externo['ts'] = pd.to_datetime(df_externo['timestamp'], dayfirst=True, errors="coerce")
            df_logger['ts'] = pd.to_datetime(df_logger['Fecha'].astype(str) + ' ' + df_logger['Hora'].astype(str), dayfirst=True, errors="coerce")
            
            df_logger = self._clean_sensor_noise(df_logger)

            # 4. Manejo inteligente de la ventana temporal
            if not start_date or not end_date:
                sd = max(df_plc['ts'].dropna().min(), df_logger['ts'].dropna().min(), df_externo['ts'].dropna().min())
                ed = min(df_plc['ts'].dropna().max(), df_logger['ts'].dropna().max(), df_externo['ts'].dropna().max())
            else:
                sd, ed = pd.to_datetime(start_date), pd.to_datetime(end_date)
                if sd > ed:
                    sd, ed = ed, sd

            df_plc = df_plc[(df_plc['ts'] >= sd) & (df_plc['ts'] <= ed)].sort_values('ts')
            df_logger = df_logger[(df_logger['ts'] >= sd) & (df_logger['ts'] <= ed)].sort_values('ts')
            df_externo = df_externo[(df_externo['ts'] >= sd) & (df_externo['ts'] <= ed)].sort_values('ts')

            if df_plc.empty or df_logger.empty or df_externo.empty:
                raise ValueError("La ventana temporal no contiene registros coincidentes.")
            
            # 5. Sincronización Temporal Avanzada
            merged = pd.merge_asof(df_plc, df_externo, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            merged = pd.merge_asof(merged, df_logger, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            
            keep_cols = ['ts', 'f20911t', 'f20911h', 'f20910p', 'f209potsecador', 'temp_ext', 'hum_ext', 'Temperatura', 'Humedad']
            merged = merged[keep_cols]
            
            for col in keep_cols:
                if col != 'ts':
                    merged[col] = pd.to_numeric(merged[col], errors='coerce')
            
            merged.set_index('ts', inplace=True)
            merged = merged.resample('1min').interpolate(method='linear')
            merged.reset_index(inplace=True)
            
            # 6. Polimorfismo de Escala de Presión
            p_mean = merged['f20910p'].mean()
            if p_mean < 800:
                p_supply_dynamic = 1013.25 + (merged['f20910p'] / 100.0)
            else:
                p_supply_dynamic = merged['f20910p']
            
            # 7. Capa de Lógica Termodinámica
            merged['w_ext'] = merged.apply(lambda x: self._calculate_psychrometrics(x['temp_ext'], x['hum_ext'], 1013.25), axis=1)
            merged['w_sala'] = merged.apply(lambda x: self._calculate_psychrometrics(x['Temperatura'], x['Humedad'], 1013.50), axis=1)
            merged['w_uma'] = merged.apply(lambda x: self._calculate_psychrometrics(x['f20911t'], x['f20911h'], p_supply_dynamic.loc[x.name]), axis=1)
            
            merged = merged.fillna(0.0)
            return self._save_records(merged, sd, ed)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Fallo crítico en el pipeline de datos: {str(e)}")
            
            try:
                error_msg = str(e)
                tipo_error = "ERROR"
                if "KeyError" in error_msg or "not found" in error_msg:
                    tipo_error = "ERROR COLUMNAS"
                elif "ValueError" in error_msg:
                    tipo_error = "ERROR FORMATO"

                log_error = DataIngestionLog(rango_datos="N/A", registros=0, estado=tipo_error)
                self.db.add(log_error)
                self.db.commit() 
            except Exception as log_err:
                self.db.rollback()
                logger.error(f"No se pudo guardar el log de error: {log_err}")

            raise HTTPException(status_code=400, detail=f"Error en pipeline de datos: {str(e)}")
        
    def _save_records(self, df: pd.DataFrame, sd, ed) -> dict:
        records = []
        for _, row in df.iterrows():
            record = HvacHistoricalData(
                timestamp=row['ts'],
                temp_ext=row['temp_ext'],
                w_ext=row['w_ext'],
                temp_uma=row['f20911t'],
                w_uma=row['w_uma'],
                potencia_secador=row['f209potsecador'],
                temp_sala=row['Temperatura'],
                hum_sala=row['Humedad'],
                w_sala=row['w_sala']
            )
            records.append(record)
        
        self.db.bulk_save_objects(records)
        rango_str = f"{sd.strftime('%d/%m')} - {ed.strftime('%d/%m')}"
        
        log_ingesta = DataIngestionLog(
            rango_datos=rango_str,
            registros=len(records),
            estado="SINCRONIZADO"
        )
        
        self.db.add(log_ingesta)
        self.db.commit()
        
        return {
            "status": "success", 
            "message": f"Sincronización completa. Se almacenó la serie temporal continua con {len(records)} registros."
        }