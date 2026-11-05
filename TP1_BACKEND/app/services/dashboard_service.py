import logging

import numpy as np
import pandas as pd

from app.ml_engine.ssd_filter import SSDFilter
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.hvac_repository import HvacRepository
from app.repositories.ml_model_version_repository import MlModelVersionRepository

logger = logging.getLogger(__name__)

MAX_POINTS_PER_POWER_LEVEL = 25


class DashboardService:
    # 🎯 RECIBE REPOSITORIOS, NO LA SESIÓN SQL
    def __init__(
        self,
        sim_repo: SimulationRepository,
        hvac_repo: HvacRepository,
        model_repo: MlModelVersionRepository | None = None,
    ):
        self.model_repo = model_repo
        self.sim_repo = sim_repo
        self.hvac_repo = hvac_repo

    def _thermal_signature(self) -> list[dict]:
        """Puntos estacionarios históricos (humedad g/kg vs potencia %), submuestreados por nivel de potencia."""
        rows = self.hvac_repo.get_power_humidity_series()
        if not rows:
            return []

        df = pd.DataFrame(rows, columns=["ts", "dryer_power", "room_w"])
        stable = SSDFilter.extract_stationary_minutes(df)
        if stable.empty:
            return []

        points = []
        for power, group in stable.groupby("dryer_power"):
            if len(group) > MAX_POINTS_PER_POWER_LEVEL:
                idx = np.linspace(0, len(group) - 1, MAX_POINTS_PER_POWER_LEVEL).astype(int)
                group = group.iloc[idx]
            points.extend(
                {"hum": round(float(w), 3), "pwr": float(power)} for w in group["room_w"]
            )
        return points

    def get_plant_analytics(self, r2_score_current: float | None = None) -> dict:
        """
        Calcula la analítica de BI a partir de las bitácoras operativas
        para alimentar el Dashboard gerencial en Next.js.
        """
        try:
            # 1. Obtenemos las últimas 24 simulaciones registradas
            # Solo recomendaciones aplicadas: un descarte no actualiza gráfica ni indicadores (HU013-2)
            simulations = self.sim_repo.get_recent_applied_simulations(limit=24)

            # R² del modelo Champion vigente en BD (se actualiza tras cada reentrenamiento)
            champion = self.model_repo.get_champion_model() if self.model_repo else None
            if champion is not None and champion.r2_score is not None:
                r2_score_current = champion.r2_score

            audit_data = []
            ahorro_acumulado = 0.0
            diferencial_kwh = 0.0

            if simulations:
                for idx, sim in enumerate(reversed(simulations)):
                    # Mapeo para el gráfico AreaChart: Real vs Recomendado
                    ideal_pwr = float(sim.recommended_power)
                    # "Real" = potencia que el PLC operaba antes de la decisión
                    real_pwr = float(sim.current_power)

                    audit_data.append(
                        {
                            "sample_id": f"S-{idx+1}",
                            "real": real_pwr,
                            "ideal": ideal_pwr,
                        }
                    )

                    # Si la planta operaba por encima de lo ideal, hay sobreconsumo evitable
                    if real_pwr > ideal_pwr:
                        ahorro_acumulado += real_pwr - ideal_pwr

                # Cálculo ficticio de kWh desperdiciados basado en la diferencia porcentual
                diferencial_kwh = round(ahorro_acumulado * 1.5, 1)

            # 2. Obtenemos puntos estables para la gráfica de firma térmica (ScatterChart)
            model_correlation = self._thermal_signature()

            # 3. Retornamos la estructura exacta que espera DashboardMetrics en el Frontend
            return {
                "kpi_ahorro": round(ahorro_acumulado, 1),
                "kpi_diferencial": diferencial_kwh,
                "r2_score": (
                    round(float(r2_score_current), 2) if r2_score_current else 0.0
                ),
                "auditData": audit_data,
                "modelCorrelation": model_correlation,
            }

        except Exception as e:
            logger.error(f"❌ Fallo al procesar la analítica del Dashboard: {e}")
            raise e
