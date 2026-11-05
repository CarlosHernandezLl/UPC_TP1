import io
import uuid
import logging
import pandas as pd
from typing import Tuple, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from app.ml_engine.ssd_filter import SSDFilter
from app.models.hvac_historical_data import HvacHistoricalData
from app.repositories.data_ingestion_repository import DataIngestionRepository
from app.repositories.hvac_repository import HvacRepository

logger = logging.getLogger(__name__)


# Columnas obligatorias por archivo (HU0001-2)
REQUIRED_COLUMNS = {
    "DATOS PLC": ["fecha", "f20911t", "f20911h", "f20910p", "f209potsecador"],
    "DATALOGGER SALA": ["Fecha", "Hora", "Temperatura", "Humedad"],
    "CLIMA EXTERIOR": ["timestamp", "temp_ext", "hum_ext"],
}


MAX_INVALID_DATE_RATIO = 0.10
OLE2_SIGNATURE = bytes.fromhex("d0cf11e0a1b11ae1")  # firma de los .xls binarios de Excel


class ColumnasFaltantesError(ValueError):
    """Error de validación estructural: indica archivo y columnas ausentes."""


class DataService:
    def __init__(
        self, hvac_repo: HvacRepository, ingestion_repo: DataIngestionRepository
    ):
        self.hvac_repo = hvac_repo
        self.ingestion_repo = ingestion_repo

    @staticmethod
    def _validate_required_columns(sources: dict):
        problems = []
        for name, (df, required) in sources.items():
            missing = [c for c in required if c not in df.columns]
            if missing:
                problems.append(f"{name}: falta(n) la(s) columna(s) {', '.join(missing)}")
        if problems:
            raise ColumnasFaltantesError(
                "Estructura inválida. " + "; ".join(problems) + ". Corrija el archivo y vuelva a cargarlo."
            )

    @staticmethod
    def _is_legacy_xls(raw: bytes) -> bool:
        """Los .xls binarios de Excel (OLE2) empiezan con esta firma."""
        return raw[:8] == OLE2_SIGNATURE

    @classmethod
    def _is_text_export(cls, filename: str, raw: bytes) -> bool:
        """El datalogger exporta .xls/.csv/.txt como texto tabulado; .xlsx y .xls binario son Excel real."""
        name = (filename or "").lower()
        if name.endswith(".xlsx") or cls._is_legacy_xls(raw):
            return False
        return name.endswith((".csv", ".txt", ".xls"))

    @classmethod
    def _read_tabular(cls, filename: str, raw: bytes) -> pd.DataFrame:
        """Lee un archivo del PLC o del clima exterior en formato .csv o .xlsx."""
        name = (filename or "").lower()
        if name.endswith(".xlsx"):
            return pd.read_excel(io.BytesIO(raw), engine="openpyxl")
        if cls._is_legacy_xls(raw):
            return pd.read_excel(io.BytesIO(raw), engine="xlrd")
        return pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding="utf-8")

    @staticmethod
    def _validate_dates(sources: dict) -> None:
        """Rechaza archivos cuya columna de fecha no tiene el formato esperado (DD/MM/AAAA HH:MM).

        Solo cuentan las filas con una fecha escrita: las filas vacías al final del datalogger no son un error.
        """
        for name, (raw, parsed) in sources.items():
            written = raw.notna()
            invalid = (parsed.isna() & written).sum()
            if not written.any() or invalid / written.sum() > MAX_INVALID_DATE_RATIO:
                raise ValueError(
                    f"Formato de fecha inválido en {name}: se espera DD/MM/AAAA HH:MM."
                )

    def _clean_sensor_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        if "Humedad" in df.columns:
            df = df[(df["Humedad"] >= 0) & (df["Humedad"] <= 100)]
        if "Temperatura" in df.columns:
            df = df[(df["Temperatura"] >= -10) & (df["Temperatura"] <= 60)]
        return df

    async def upload_and_sync(
        self,
        file_plc,
        file_logger,
        file_externo,
        start_date: str = None,
        end_date: str = None,
    ) -> dict:
        try:
            plc_bytes = await file_plc.read()
            logger_bytes = await file_logger.read()
            externo_bytes = await file_externo.read()

            df_plc = self._read_tabular(file_plc.filename, plc_bytes)
            df_externo = self._read_tabular(file_externo.filename, externo_bytes)

            if self._is_text_export(file_logger.filename, logger_bytes):
                df_logger = pd.read_csv(
                    io.BytesIO(logger_bytes), sep="\t", skiprows=20, encoding="latin1"
                )
                if not df_logger.empty:
                    df_logger = df_logger.drop([0, 1, 2]).reset_index(drop=True)
            else:
                df_logger = pd.read_excel(
                    io.BytesIO(logger_bytes),
                    skiprows=20,
                    engine="xlrd" if self._is_legacy_xls(logger_bytes) else "openpyxl",
                )

            for df_node in [df_plc, df_logger, df_externo]:
                df_node.columns = df_node.columns.str.strip()

            self._validate_required_columns(
                {
                    "DATOS PLC": (df_plc, REQUIRED_COLUMNS["DATOS PLC"]),
                    "DATALOGGER SALA": (df_logger, REQUIRED_COLUMNS["DATALOGGER SALA"]),
                    "CLIMA EXTERIOR": (df_externo, REQUIRED_COLUMNS["CLIMA EXTERIOR"]),
                }
            )

            df_plc["ts"] = pd.to_datetime(
                df_plc["fecha"], dayfirst=True, errors="coerce"
            )
            df_externo["ts"] = pd.to_datetime(
                df_externo["timestamp"], dayfirst=True, errors="coerce"
            )
            df_logger["ts"] = pd.to_datetime(
                df_logger["Fecha"].astype(str) + " " + df_logger["Hora"].astype(str),
                dayfirst=True,
                errors="coerce",
            )

            self._validate_dates(
                {
                    "DATOS PLC": (df_plc["fecha"], df_plc["ts"]),
                    "DATALOGGER SALA": (df_logger["Fecha"], df_logger["ts"]),
                    "CLIMA EXTERIOR": (df_externo["timestamp"], df_externo["ts"]),
                }
            )

            df_logger = self._clean_sensor_noise(df_logger)

            def clean_date_param(val: str):
                if not val or str(val).strip().lower() in [
                    "",
                    "string",
                    "null",
                    "none",
                    "undefined",
                ]:
                    return None
                return pd.to_datetime(val, errors="coerce")

            sd_input = clean_date_param(start_date)
            ed_input = clean_date_param(end_date)

            # Rango común de los tres archivos; cada fecha informada reemplaza a su extremo (puede darse solo una)
            sd_auto = max(
                df_plc["ts"].dropna().min(),
                df_logger["ts"].dropna().min(),
                df_externo["ts"].dropna().min(),
            )
            ed_auto = min(
                df_plc["ts"].dropna().max(),
                df_logger["ts"].dropna().max(),
                df_externo["ts"].dropna().max(),
            )
            sd = sd_input if sd_input is not None and not pd.isna(sd_input) else sd_auto
            ed = ed_input if ed_input is not None and not pd.isna(ed_input) else ed_auto

            if sd >= ed and sd_input is not None and ed_input is not None:
                raise ValueError("La fecha de fin debe ser mayor a la fecha de inicio.")
            logger.info(f"📅 Rango temporal aplicado: {sd} hasta {ed}")

            df_plc = df_plc[(df_plc["ts"] >= sd) & (df_plc["ts"] <= ed)].sort_values(
                "ts"
            )
            df_logger = df_logger[
                (df_logger["ts"] >= sd) & (df_logger["ts"] <= ed)
            ].sort_values("ts")
            df_externo = df_externo[
                (df_externo["ts"] >= sd) & (df_externo["ts"] <= ed)
            ].sort_values("ts")

            if df_plc.empty or df_logger.empty or df_externo.empty:
                raise ValueError(
                    "La ventana temporal no contiene registros coincidentes entre los 3 archivos."
                )

            merged = pd.merge_asof(
                df_plc,
                df_externo,
                on="ts",
                direction="nearest",
                tolerance=pd.Timedelta("1min"),
            )
            merged = pd.merge_asof(
                merged,
                df_logger,
                on="ts",
                direction="nearest",
                tolerance=pd.Timedelta("1min"),
            )

            keep_cols = [
                "ts",
                "f20911t",
                "f20911h",
                "f20910p",
                "f209potsecador",
                "temp_ext",
                "hum_ext",
                "Temperatura",
                "Humedad",
            ]
            merged = merged[keep_cols]

            for col in keep_cols:
                if col != "ts":
                    merged[col] = pd.to_numeric(merged[col], errors="coerce")

            merged.set_index("ts", inplace=True)
            merged = merged.resample("1min").interpolate(method="linear").reset_index()

            # p_mean = merged["f20910p"].mean()
            p_supply_dynamic = SSDFilter.calculate_dynamic_ahu_pressure(
                merged["f20910p"]
            )

            merged["w_ext"] = merged.apply(
                lambda x: SSDFilter.calculate_absolute_humidity(
                    x["temp_ext"], x["hum_ext"], 1013.25
                ),
                axis=1,
            )
            merged["w_sala"] = merged.apply(
                lambda x: SSDFilter.calculate_absolute_humidity(
                    x["Temperatura"], x["Humedad"], 1013.50
                ),
                axis=1,
            )
            merged["w_uma"] = merged.apply(
                lambda x: SSDFilter.calculate_absolute_humidity(
                    x["f20911t"], x["f20911h"], p_supply_dynamic.loc[x.name]
                ),
                axis=1,
            )

            # merged = merged.fillna(0.0)
            merged = merged.dropna()

            # 🚀 GENERACIÓN DE ID ÚNICO DE LOTE PARA MLOpS
            # batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M')}-{uuid.uuid4().hex[:6].upper()}"
            batch_id = uuid.uuid4()
            return self._save_records(merged, sd, ed, batch_id)

        except Exception as e:
            logger.error(f"❌ Fallo en pipeline de datos: {str(e)}")
            if isinstance(e, ColumnasFaltantesError):
                tipo_error = "ERROR COLUMNAS"
                detalle = str(e)
            elif isinstance(e, KeyError) or "not in index" in str(e):
                tipo_error = "ERROR COLUMNAS"
                detalle = f"Faltan columnas requeridas en los archivos cargados: {str(e).strip(chr(34))}"
            else:
                tipo_error = "ERROR FORMATO"
                detalle = str(e)

            try:
                self.ingestion_repo.create(
                    {
                        "data_range": "N/A",
                        "record_count": 0,
                        "status": tipo_error,
                        "ingested_at": datetime.now(ZoneInfo("America/Lima")),
                    }
                )
            except Exception as log_ex:
                logger.error(f"❌ Error al guardar log de fallo: {log_ex}")

            raise HTTPException(
                status_code=400, detail=f"Error al sincronizar archivos: {detalle}"
            )

    def _save_records(self, df: pd.DataFrame, sd, ed, batch_id: str) -> dict:
        records = []
        for _, row in df.iterrows():
            record = HvacHistoricalData(
                timestamp=row["ts"],
                batch_id=batch_id,  # 🎯 Alineado a nuestro nuevo modelo
                outdoor_temp=row["temp_ext"],
                outdoor_w=row["w_ext"],
                ahu_temp=row["f20911t"],
                ahu_w=row["w_uma"],
                injection_pressure=row["f20910p"],
                dryer_power=row["f209potsecador"],
                room_temp=row["Temperatura"],
                room_rh=row["Humedad"],
                room_w=row["w_sala"],
                is_clean=True,
            )
            records.append(record)

        self.hvac_repo.bulk_save(records)
        rango_str = f"{sd.strftime('%d/%m/%Y')} - {ed.strftime('%d/%m/%Y')}"

        self.ingestion_repo.create(
            {
                "batch_id": batch_id,  # 🎯 AHORA SÍ QUEDA REGISTRADO EL LINAJE
                "data_range": rango_str,
                "record_count": len(records),
                "status": "SINCRONIZADO",
                "ingested_at": datetime.now(ZoneInfo("America/Lima")),
            }
        )

        return {
            "status": "success",
            "batch_id": batch_id,
            "message": f"Sincronización completa. Lote {batch_id} guardado con {len(records)} registros en hora Lima.",
        }

    def get_ingestion_history(self):
        """Método puente para que el controlador no consulte el repositorio directamente."""
        return self.ingestion_repo.get_all_history()

    def get_latest_training_batch(self) -> Tuple[Optional[str], List[any]]:
        """
        🚀 MLOps GxP: Obtiene el UUID del último lote sincronizado y sus registros históricos
        para alimentar el reentrenamiento científico del modelo XGBoost.
        """
        logger.info(
            "🔍 [DataService] Buscando el último lote de datos ingestado para MLOps..."
        )

        # 1. Consultar el último registro de sincronización en la tabla de logs de ingesta
        latest_log = self.ingestion_repo.get_latest_sync()

        # La última ingesta debe haber sido exitosa: no se reentrena sobre una carga errónea
        if latest_log and latest_log.status != "SINCRONIZADO":
            raise ValueError(
                f"La última carga de datos falló ({latest_log.status}). "
                "Cargue un dataset válido en Ingesta de Datos antes de reentrenar."
            )

        # Si no hay registros de carga web, intentamos un fallback seguro con los últimos 5000 registros
        if not latest_log or not getattr(latest_log, "batch_id", None):
            logger.warning(
                "⚠️ No se encontró un log de ingesta con batch_id. Extrayendo histórico general..."
            )
            records = self.hvac_repo.get_latest(limit=5000)
            return None, records if records else []

        batch_id = str(latest_log.batch_id)
        logger.info(
            f"📦 [DataService] Lote detectado: UUID={batch_id}. Extrayendo telemetría..."
        )

        # 2. Consultar los registros climáticos y de planta asociados exactamente a ese UUID
        records = self.hvac_repo.get_by_batch_id(latest_log.batch_id)

        if not records:
            logger.warning(
                f"⚠️ El lote {batch_id} existe en logs pero su tabla histórica está vacía. Activando fallback..."
            )
            records = self.hvac_repo.get_latest(limit=5000)
            return batch_id, records if records else []

        logger.info(
            f"✨ [DataService] Se extrajeron {len(records)} registros del lote {batch_id} exitosamente."
        )
        return batch_id, records
