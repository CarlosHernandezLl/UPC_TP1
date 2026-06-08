# app/services/data_service.py
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np
import io
import logging
from fastapi import HTTPException
from app.models.hvac_model import HvacHistoricalData

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

    async def upload_and_sync(self, file_plc, file_logger, file_externo, start_date: str = None, end_date: str = None) -> dict:
        try:
            # 1. Lectura asíncrona de los flujos binarios desde el Frontend
            plc_bytes = await file_plc.read()
            logger_bytes = await file_logger.read()
            externo_bytes = await file_externo.read()
            
            # 2. Conversión a DataFrames de Pandas evaluando el formato del Datalogger
            df_plc = pd.read_csv(io.BytesIO(plc_bytes), sep=',')
            df_externo = pd.read_csv(io.BytesIO(externo_bytes), sep=',')
            
            filename_log = file_logger.filename.lower()
            if filename_log.endswith((".csv", ".txt")):
                # Manejo del datalogger Rotronic tabulado (Saltando metadatos de configuración)
                df_logger = pd.read_csv(io.BytesIO(logger_bytes), sep="\t", skiprows=20, encoding="latin1")
            else:
                df_logger = pd.read_excel(io.BytesIO(logger_bytes), skiprows=20, engine="openpyxl")
            
            # Normalización y limpieza de espacios en las cabeceras de columnas
            for df_node in [df_plc, df_logger, df_externo]:
                df_node.columns = df_node.columns.str.strip()
            
            # 3. Estandarización y homogeneización de marcas de tiempo (Timestamps)
            df_plc['ts'] = pd.to_datetime(df_plc['fecha'], errors="coerce")
            df_externo['ts'] = pd.to_datetime(df_externo['timestamp'], errors="coerce")
            df_logger['ts'] = pd.to_datetime(df_logger['Fecha'] + ' ' + df_logger['Hora'], errors="coerce")
            
            # Limpieza temprana de ruido físico en datalogger
            df_logger = self._clean_sensor_noise(df_logger)

            # 4. CORRECCIÓN: Manejo inteligente de la ventana temporal (Solape Automático)
            if not start_date or not end_date:
                logger.info("⚠️ No se proporcionaron fechas de corte. Calculando área de intersección común de hardware...")
                # El inicio común es el máximo de los valores mínimos válidos disponibles
                sd = max(df_plc['ts'].dropna().min(), df_logger['ts'].dropna().min(), df_externo['ts'].dropna().min())
                # El fin común es el mínimo de los valores máximos válidos disponibles
                ed = min(df_plc['ts'].dropna().max(), df_logger['ts'].dropna().max(), df_externo['ts'].dropna().max())
                logger.info(f"📅 Rango de solape auto-detectado: Desde {sd} hasta {ed}")
            else:
                # Si el usuario ingresó fechas desde la interfaz web, las parseamos
                sd, ed = pd.to_datetime(start_date), pd.to_datetime(end_date)
                if sd > ed:
                    sd, ed = ed, sd

            # Segmentar los DataFrames individuales bajo el horizonte temporal validado
            df_plc = df_plc[(df_plc['ts'] >= sd) & (df_plc['ts'] <= ed)].sort_values('ts')
            df_logger = df_logger[(df_logger['ts'] >= sd) & (df_logger['ts'] <= ed)].sort_values('ts')
            df_externo = df_externo[(df_externo['ts'] >= sd) & (df_externo['ts'] <= ed)].sort_values('ts')

            if df_plc.empty or df_logger.empty or df_externo.empty:
                raise ValueError("La ventana temporal calculada o solicitada no contiene registros coincidentes en las tres fuentes.")
            
            # 5. Sincronización Temporal Avanzada mediante remuestreo e interpolación lineal a 1 minuto
            merged = pd.merge_asof(df_plc, df_externo, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            merged = pd.merge_asof(merged, df_logger, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            
            keep_cols = ['ts', 'f20911t', 'f20911h', 'f20910p', 'f209potsecador', 'temp_ext', 'hum_ext', 'Temperatura', 'Humedad']
            merged = merged[keep_cols]
            
            for col in keep_cols:
                if col != 'ts':
                    merged[col] = pd.to_numeric(merged[col], errors='coerce')
            
            # Forzar remuestreo explícito a grilla exacta de 1 minuto e interpolar nulos menores
            merged.set_index('ts', inplace=True)
            merged = merged.resample('1min').interpolate(method='linear')
            merged.reset_index(inplace=True)
            
            # 6. Resolución del Polimorfismo de Escala de Presión del PLC (Ecuación 5 del Paper)
            p_mean = merged['f20910p'].mean()
            if p_mean < 800:
                # Entrada en Pascales relativos (ej. 150 Pa) -> Convertir a hPa absoluto dinámico
                p_supply_dynamic = 1013.25 + (merged['f20910p'] / 100.0)
            else:
                # Entrada en Hectopascales absolutos directos
                p_supply_dynamic = merged['f20910p']
            
            # 7. Ingesta de la Capa de Lógica Termodinámica
            merged['w_ext'] = merged.apply(lambda x: self._calculate_psychrometrics(x['temp_ext'], x['hum_ext'], 1013.25), axis=1)
            merged['w_sala'] = merged.apply(lambda x: self._calculate_psychrometrics(x['Temperatura'], x['Humedad'], 1013.50), axis=1)
            merged['w_uma'] = merged.apply(lambda x: self._calculate_psychrometrics(x['f20911t'], x['f20911h'], p_supply_dynamic.loc[x.name]), axis=1)
            
            # Tratar residuos nulos post-interpolación
            merged = merged.fillna(0.0)

            # 8. Volcado masivo y persistencia bajo transaccionalidad segura en Base de Datos
            return self._save_records(merged)

        except Exception as e:
            self.db.rollback()
            logger.error(f"Fallo crítico en el pipeline de datos del Gemelo Digital: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error en pipeline de datos: {str(e)}")
        
    def _save_records(self, df: pd.DataFrame) -> dict:
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
                hum_sala=row['Humedad']
            )
            records.append(record)
        
        self.db.bulk_save_objects(records)
        self.db.commit()
        return {"status": "success", "message": f"Pipeline completado con éxito. {len(records)} registros sincronizados e insertados."}