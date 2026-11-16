import os
import logging
import numpy as np
import pandas as pd
import xgboost as xgb
from app.ml_engine.ssd_filter import SSDFilter

logger = logging.getLogger(__name__)


class SimulatorEngine:
    """Motor de IA en memoria RAM para inferencia de control HVAC farmacéutico (12 Variables)."""

    def __init__(self):
        self.model = xgb.XGBRegressor()
        self.r2_score = None
        self.rmse = None
        self.model_loaded = False
        self.loaded_version: str | None = None
        self.loaded_origin: str | None = None
        self.feature_cols = [
            "dryer_power", 
            "outdoor_temp",
            "outdoor_w",
            "ahu_temp",
            "ahu_w",
            "injection_pressure",
        ]
        self._load_initial_model()

    def _load_initial_model(self):
        """Fallback de emergencia SOLO si aún no hay ningún Champion en BD.
        La fuente de verdad real se carga en el startup de FastAPI — ver bootstrap_champion_model().
        """
        base_path = os.path.dirname(__file__)
        model_path = os.path.join(base_path, "saved_models", "xgboost_hvac_v1.json")
        self.reload_model_in_memory(model_path, version_tag="base", origin="modelo base")

    def _align_feature_names(self) -> None:
        """Los modelos antiguos usan otros nombres de variable (mismo orden): se renombran a los vigentes."""
        booster = self.model.get_booster()
        if (
            booster.num_features() == len(self.feature_cols)
            and list(booster.feature_names or []) != self.feature_cols
        ):
            booster.feature_names = list(self.feature_cols)

    def loaded_model_info(self) -> dict:
        """Qué modelo está realmente en RAM (para mostrarlo en /mlops/metrics)."""
        return {
            "cargado": self.model_loaded,
            "version_tag": self.loaded_version,
            "origen": self.loaded_origin,
        }

    def reload_model_from_json(
        self, raw_model: str, version_tag: str | None = None, origin: str = "base de datos"
    ) -> bool:
        """Carga el modelo desde su contenido JSON (almacenado en la BD, sin depender del disco)."""
        try:
            self.model.load_model(bytearray(raw_model.encode("utf-8")))
            self._align_feature_names()
            self.model_loaded = True
            self.loaded_version, self.loaded_origin = version_tag, origin
            logger.info(f"[SimulatorEngine] Modelo {version_tag} cargado desde {origin}.")
            return True
        except Exception as e:
            logger.error(f"[SimulatorEngine] No se pudo cargar el modelo desde {origin}: {e}")
            self.model_loaded = False
            return False

    def reload_model_in_memory(
        self,
        model_path: str = None,
        version_tag: str | None = None,
        origin: str = "archivo",
    ) -> bool:
        """Carga o recarga pesos XGBoost en caliente sin reiniciar el servidor FastAPI."""
        try:
            if not model_path:
                base_path = os.path.dirname(__file__)
                model_path = os.path.join(
                    base_path, "saved_models", "xgboost_hvac_v1.json"
                )

            if os.path.exists(model_path):
                self.model.load_model(model_path)
                self._align_feature_names()
                self.model_loaded = True
                self.loaded_version, self.loaded_origin = version_tag, origin
                logger.info(
                    f"✨ [SimulatorEngine] Modelo XGBoost (12 Variables) cargado en RAM desde: {model_path}"
                )
                return True
            else:
                logger.warning(
                    f"⚠️ [SimulatorEngine] No se encontró el archivo de modelo en {model_path}. Inferencia en modo degradado."
                )
                self.model_loaded = False
                return False
        except Exception as e:
            logger.error(
                f"❌ [SimulatorEngine] Error crítico al cargar pesos XGBoost: {str(e)}"
            )
            self.model_loaded = False
            return False

    def recomendar_potencia(
        self,
        current_power: float,
        room_temp: float,
        target_setpoint: float,
        outdoor_temp: float,
        outdoor_rh: float,
        ahu_temp: float,
        ahu_rh: float,
        injection_pressure: float,
        min_power_allowed: float = 5.0,
        safety_margin_gkg: float = 0.37,  # 🚀 NUEVO MARGEN DIRECTO (Decisión 1)
        min_gmp_rh_limit: float = 40.0,
        max_gmp_rh_limit: float = 55.0,
    ) -> tuple[float, bool]:

        # La recomendación es siempre un entero entre 0 y 100 (HU011-1)
        current_power = float(round(current_power))

        if not self.model_loaded:
            return current_power, False

        w_ext = SSDFilter.calculate_absolute_humidity(outdoor_temp, outdoor_rh, 1013.25)
        p_dynamic = SSDFilter.calculate_dynamic_ahu_pressure(injection_pressure)
        w_uma = SSDFilter.calculate_absolute_humidity(ahu_temp, ahu_rh, p_dynamic)

        # Cálculo del límite higrométrico objetivo en g/kg
        w_objetivo_estricto = SSDFilter.calculate_absolute_humidity(
            room_temp, target_setpoint, 1013.50
        )
        w_limite_busqueda = w_objetivo_estricto - safety_margin_gkg

        best_power = current_power
        power_candidates = np.arange(int(current_power), int(min_power_allowed) - 1, -1)

        for p in power_candidates:
            # 🚀 INFERENCIA LIMPIA CON 6 VARIABLES
            df_input = pd.DataFrame(
                [[p, outdoor_temp, w_ext, ahu_temp, w_uma, injection_pressure]],
                columns=self.feature_cols,
            )
            w_sala_pred = float(self.model.predict(df_input)[0])

            if w_sala_pred <= w_limite_busqueda:
                best_power = float(p)
            else:
                break

        # Verificación GxP Final
        df_final_check = pd.DataFrame(
            [[best_power, outdoor_temp, w_ext, ahu_temp, w_uma, injection_pressure]],
            columns=self.feature_cols,
        )
        w_final = float(self.model.predict(df_final_check)[0])
        es_sala = 6.1121 * np.exp(
            (18.678 - room_temp / 234.5) * (room_temp / (257.14 + room_temp))
        )
        k_final = w_final / 622.0
        e_final = (1013.50 * k_final) / (1.0 + k_final)
        hr_final_sim = (e_final / es_sala) * 100.0

        # Alerta si la humedad lograda por el modelo O el setpoint solicitado salen de la banda GMP
        def outside_band(rh: float) -> bool:
            return rh < min_gmp_rh_limit or rh > max_gmp_rh_limit

        is_gmp_alert = outside_band(hr_final_sim) or outside_band(target_setpoint)
        return best_power, is_gmp_alert

simulator_engine_instance = SimulatorEngine()