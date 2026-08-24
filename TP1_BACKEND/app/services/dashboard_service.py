import logging
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.hvac_repository import HvacRepository

logger = logging.getLogger(__name__)


class DashboardService:
    # 🎯 RECIBE REPOSITORIOS, NO LA SESIÓN SQL
    def __init__(self, sim_repo: SimulationRepository, hvac_repo: HvacRepository):
        self.sim_repo = sim_repo
        self.hvac_repo = hvac_repo

    def get_plant_analytics(self, r2_score_current: float) -> dict:
        """
        Calcula la analítica de BI a partir de las bitácoras operativas
        para alimentar el Dashboard gerencial en Next.js.
        """
        try:
            # 1. Obtenemos las últimas 24 simulaciones registradas
            # Asumiendo que tienes un método get_recent_simulations(limit) en tu repositorio
            simulations = self.sim_repo.get_recent_simulations(limit=24)

            audit_data = []
            ahorro_acumulado = 0.0
            diferencial_kwh = 0.0

            if simulations:
                for idx, sim in enumerate(reversed(simulations)):
                    # Mapeo para el gráfico AreaChart: Real vs Recomendado
                    ideal_pwr = float(sim.recommended_power)
                    real_pwr = float(sim.applied_power)

                    audit_data.append(
                        {
                            "sample_id": f"S-{idx+1}",
                            "real": real_pwr,
                            "ideal": ideal_pwr,
                        }
                    )

                    # Si el humano aplicó más de lo ideal, calculamos el desperdicio
                    if real_pwr > ideal_pwr:
                        ahorro_acumulado += real_pwr - ideal_pwr

                # Cálculo ficticio de kWh desperdiciados basado en la diferencia porcentual
                diferencial_kwh = round(ahorro_acumulado * 1.5, 1)

            # 2. Obtenemos puntos estables para la gráfica de firma térmica (ScatterChart)
            hvac_data = self.hvac_repo.get_latest(limit=100)
            model_correlation = []

            if hvac_data:
                for record in hvac_data:
                    model_correlation.append(
                        {"hum": float(record.room_w), "pwr": float(record.dryer_power)}
                    )

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
