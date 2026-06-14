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
    # MÓDULO IA: FILTROS DE ESTADO ESTACIONARIO (SSD)
    # =================================================================
    def _calcular_umbral_optimo_estadistico(self, df: pd.DataFrame, percentil=0.90) -> float:
        """Analiza la derivada temporal para proponer un umbral de estabilidad dinámico."""
        diff_w = df['w_sala'].diff().abs().dropna()
        smooth_diff = diff_w.rolling(window=5, min_periods=1).mean()
        return float(smooth_diff.quantile(percentil))

    def _extraer_minutos_estacionarios(self, df: pd.DataFrame, paciencia=10) -> pd.DataFrame:
        """Aplica el algoritmo SSD para extraer únicamente las ventanas estables (Data de Oro)."""
        df = df.copy()
        df['diff_w'] = df['w_sala'].diff().abs()
        df['cambio_escalon'] = (df['f209potsecador'] != df['f209potsecador'].shift()).cumsum()

        umbral_estabilidad = self._calcular_umbral_optimo_estadistico(df, percentil=0.90)
        lista_df_estables = []

        for _, grupo in df.groupby('cambio_escalon'):
            if len(grupo) < 20: 
                continue

            data_escalon = grupo.copy()
            data_escalon['smooth_diff'] = data_escalon['diff_w'].rolling(window=5, min_periods=1).mean()
            estabilidad = data_escalon['smooth_diff'] < umbral_estabilidad

            idx_estabilizacion_real = None
            conteo = 0

            for idx in data_escalon.index:
                if estabilidad.loc[idx]:
                    conteo += 1
                else:
                    conteo = 0

                if conteo >= paciencia:
                    idx_estabilizacion_real = idx
                    break

            if idx_estabilizacion_real is not None:
                datos_post_estabilizacion = data_escalon.loc[idx_estabilizacion_real:]
                data_estable = datos_post_estabilizacion[datos_post_estabilizacion['smooth_diff'] < umbral_estabilidad].copy()
                lista_df_estables.append(data_estable)

        if not lista_df_estables:
            return pd.DataFrame()

        return pd.concat(lista_df_estables).reset_index(drop=True)

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

            # =========================================================
            # 8. NÚCLEO ML: FILTRO SSD (Solo guardamos la Data de Oro)
            # =========================================================
            df_oro = self._extraer_minutos_estacionarios(merged)
            
            if df_oro.empty:
                raise ValueError("El algoritmo SSD procesó los datos pero no encontró ventanas en estado estacionario.")

            # 9. Volcado masivo a BD de los registros purificados
            return self._save_records(df_oro, sd, ed)

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
                w_sala=row['w_sala'] # <- CORRECCIÓN: Faltaba persistir w_sala
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
            "message": f"Filtro SSD completado. Se purificaron e inyectaron {len(records)} registros estacionarios de alta calidad."
        }


# # app/services/data_service.py
# from datetime import datetime

# from sqlalchemy.orm import Session
# import pandas as pd
# import numpy as np
# import io
# import logging
# from fastapi import HTTPException
# from app.models.hvac_model import DataIngestionLog, HvacHistoricalData

# logger = logging.getLogger(__name__)

# class DataService:
#     def __init__(self, db: Session):
#         self.db = db
        
#     def _calculate_psychrometrics(self, temp, hr, p_absolute):
#         """
#         Calcula la razón de humedad absoluta (W, g/kg) utilizando la formulación 
#         empírica exacta de Buck (1981) alineada al manuscrito y al diseño experimental.
#         """
#         try:
#             if pd.isna(temp) or pd.isna(hr) or pd.isna(p_absolute):
#                 return 0.0
        
#             t = float(temp)
#             rh = float(hr)
#             p = float(p_absolute)

#             # Ecuación de Buck (1981) original del modelo matemático
#             es = 6.1121 * np.exp((18.678 - t / 234.5) * (t / (257.14 + t)))
#             e = (rh / 100.0) * es
            
#             # Constante molecular precisa (epsilon = 0.62197)
#             w = 1000.0 * (0.62197 * e / (p - e))
#             return round(w, 6)
        
#         except Exception as err:
#             logger.error(f"❌ Error psicrométrico - Temp: {temp}, HR: {hr}, P: {p_absolute}. Detalle: {err}")
#             return 0.0

#     def _clean_sensor_noise(self, df: pd.DataFrame) -> pd.DataFrame:
#         """Elimina valores físicamente imposibles para evitar heterocedasticidad y sesgos."""
#         if 'Humedad' in df.columns:
#             df = df[(df['Humedad'] >= 0) & (df['Humedad'] <= 100)]
#         if 'Temperatura' in df.columns:
#             df = df[(df['Temperatura'] >= -10) & (df['Temperatura'] <= 60)]
#         return df

#     async def upload_and_sync(self, file_plc, file_logger, file_externo, start_date: str = None, end_date: str = None) -> dict:
#         try:
#             # 1. Lectura asíncrona de los flujos binarios desde el Frontend
#             plc_bytes = await file_plc.read()
#             logger_bytes = await file_logger.read()
#             externo_bytes = await file_externo.read()
            
#             # 2. Conversión a DataFrames de Pandas evaluando el formato del Datalogger
#             #df_plc = pd.read_csv(io.BytesIO(plc_bytes), sep=',')
#             #df_externo = pd.read_csv(io.BytesIO(externo_bytes), sep=',')
            
#             df_plc = pd.read_csv(io.BytesIO(plc_bytes), sep=None, engine='python', encoding='utf-8')
#             df_externo = pd.read_csv(io.BytesIO(externo_bytes), sep=None, engine='python', encoding='utf-8')
            
#             filename_log = file_logger.filename.lower()
#             if filename_log.endswith((".csv", ".txt", ".xls")):
#                 df_logger = pd.read_csv(io.BytesIO(logger_bytes), sep="\t", skiprows=20, encoding="latin1")
                
#                 if not df_logger.empty:
#                     df_logger = df_logger.drop([0, 1, 2]).reset_index(drop=True)
#             else:
#                 df_logger = pd.read_excel(io.BytesIO(logger_bytes), skiprows=20, engine="openpyxl")
                            
#             for df_node in [df_plc, df_logger, df_externo]:
#                 df_node.columns = df_node.columns.str.strip()
            
#             # 3. Estandarización y homogeneización de marcas de tiempo (Timestamps)
#             df_plc['ts'] = pd.to_datetime(df_plc['fecha'], errors="coerce")
#             df_externo['ts'] = pd.to_datetime(df_externo['timestamp'], errors="coerce")
#             df_logger['ts'] = pd.to_datetime(df_logger['Fecha'] + ' ' + df_logger['Hora'], errors="coerce")
            
#             # Limpieza temprana de ruido físico en datalogger
#             df_logger = self._clean_sensor_noise(df_logger)

#             # 4. CORRECCIÓN: Manejo inteligente de la ventana temporal (Solape Automático)
#             if not start_date or not end_date:
#                 logger.info("⚠️ No se proporcionaron fechas de corte. Calculando área de intersección común de hardware...")
#                 # El inicio común es el máximo de los valores mínimos válidos disponibles
#                 sd = max(df_plc['ts'].dropna().min(), df_logger['ts'].dropna().min(), df_externo['ts'].dropna().min())
#                 # El fin común es el mínimo de los valores máximos válidos disponibles
#                 ed = min(df_plc['ts'].dropna().max(), df_logger['ts'].dropna().max(), df_externo['ts'].dropna().max())
#                 logger.info(f"📅 Rango de solape auto-detectado: Desde {sd} hasta {ed}")
#             else:
#                 # Si el usuario ingresó fechas desde la interfaz web, las parseamos
#                 sd, ed = pd.to_datetime(start_date), pd.to_datetime(end_date)
#                 if sd > ed:
#                     sd, ed = ed, sd

#             # Segmentar los DataFrames individuales bajo el horizonte temporal validado
#             df_plc = df_plc[(df_plc['ts'] >= sd) & (df_plc['ts'] <= ed)].sort_values('ts')
#             df_logger = df_logger[(df_logger['ts'] >= sd) & (df_logger['ts'] <= ed)].sort_values('ts')
#             df_externo = df_externo[(df_externo['ts'] >= sd) & (df_externo['ts'] <= ed)].sort_values('ts')

#             if df_plc.empty or df_logger.empty or df_externo.empty:
#                 raise ValueError("La ventana temporal calculada o solicitada no contiene registros coincidentes en las tres fuentes.")
            
#             # 5. Sincronización Temporal Avanzada mediante remuestreo e interpolación lineal a 1 minuto
#             merged = pd.merge_asof(df_plc, df_externo, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
#             merged = pd.merge_asof(merged, df_logger, on='ts', direction='nearest', tolerance=pd.Timedelta('1min'))
            
#             keep_cols = ['ts', 'f20911t', 'f20911h', 'f20910p', 'f209potsecador', 'temp_ext', 'hum_ext', 'Temperatura', 'Humedad']
#             merged = merged[keep_cols]
            
#             for col in keep_cols:
#                 if col != 'ts':
#                     merged[col] = pd.to_numeric(merged[col], errors='coerce')
            
#             # Forzar remuestreo explícito a grilla exacta de 1 minuto e interpolar nulos menores
#             merged.set_index('ts', inplace=True)
#             merged = merged.resample('1min').interpolate(method='linear')
#             merged.reset_index(inplace=True)
            
#             # 6. Resolución del Polimorfismo de Escala de Presión del PLC (Ecuación 5 del Paper)
#             p_mean = merged['f20910p'].mean()
#             if p_mean < 800:
#                 # Entrada en Pascales relativos (ej. 150 Pa) -> Convertir a hPa absoluto dinámico
#                 p_supply_dynamic = 1013.25 + (merged['f20910p'] / 100.0)
#             else:
#                 # Entrada en Hectopascales absolutos directos
#                 p_supply_dynamic = merged['f20910p']
            
#             # 7. Ingesta de la Capa de Lógica Termodinámica
#             merged['w_ext'] = merged.apply(lambda x: self._calculate_psychrometrics(x['temp_ext'], x['hum_ext'], 1013.25), axis=1)
#             merged['w_sala'] = merged.apply(lambda x: self._calculate_psychrometrics(x['Temperatura'], x['Humedad'], 1013.50), axis=1)
#             merged['w_uma'] = merged.apply(lambda x: self._calculate_psychrometrics(x['f20911t'], x['f20911h'], p_supply_dynamic.loc[x.name]), axis=1)
            
#             # Tratar residuos nulos post-interpolación
#             merged = merged.fillna(0.0)

#             # 8. Volcado masivo y persistencia bajo transaccionalidad segura en Base de Datos
#             return self._save_records(merged, sd, ed)

#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Fallo crítico en el pipeline de datos del Gemelo Digital: {str(e)}")
            
#             try:
#                 # 2. Creamos un log de error legible para el usuario en Next.js
#                 error_msg = str(e)
#                 tipo_error = "ERROR"
#                 if "KeyError" in error_msg or "not found" in error_msg:
#                     tipo_error = "ERROR COLUMNAS"
#                 elif "ValueError" in error_msg:
#                     tipo_error = "ERROR FORMATO"

#                 log_error = DataIngestionLog(
#                     rango_datos="N/A",
#                     registros=0,
#                     estado=tipo_error
#                 )
#                 self.db.add(log_error)
#                 self.db.commit() # Confirmamos exclusivamente el log de error
#             except Exception as log_err:
#                 self.db.rollback()
#                 logger.error(f"No se pudo guardar el log de auditoría del error: {log_err}")

#             # 3. Lanzamos la excepción al frontend para cambiar el estado visual
#             raise HTTPException(status_code=400, detail=f"Error en pipeline de datos: {str(e)}")
        
#     def _save_records(self, df: pd.DataFrame, sd, ed) -> dict:
#         records = []
#         for _, row in df.iterrows():
#             record = HvacHistoricalData(
#                 timestamp=row['ts'],
#                 temp_ext=row['temp_ext'],
#                 w_ext=row['w_ext'],
#                 temp_uma=row['f20911t'],
#                 w_uma=row['w_uma'],
#                 potencia_secador=row['f209potsecador'],
#                 temp_sala=row['Temperatura'],
#                 hum_sala=row['Humedad']
#             )
#             records.append(record)
        
#         self.db.bulk_save_objects(records)
        
#         rango_str = f"{sd.strftime('%d/%m')} - {ed.strftime('%d/%m')}"
        
#         log_ingesta = DataIngestionLog(
#             rango_datos=rango_str,
#             registros=len(records),
#             estado="SINCRONIZADO"
#         )
        
#         self.db.add(log_ingesta)
                
#         self.db.commit()
#         return {
#             "status": "success", 
#             "message": f"Pipeline completado con éxito. {len(records)} registros sincronizados e insertados."
#         }