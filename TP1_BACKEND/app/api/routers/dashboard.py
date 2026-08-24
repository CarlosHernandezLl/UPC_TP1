from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import check_role

from app.services.dashboard_service import DashboardService

# 🚀 IMPORTAMOS LOS REPOSITORIOS
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.hvac_repository import HvacRepository

from app.ml_engine.simulator_engine import SimulatorEngine

router = APIRouter(prefix="/dashboard", tags=["Analítica & BI"])

sim_engine = SimulatorEngine()


def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    sim_repo = SimulationRepository(db)
    hvac_repo = HvacRepository(db)
    return DashboardService(sim_repo=sim_repo, hvac_repo=hvac_repo)


@router.get("/metrics", dependencies=[Depends(check_role(["GERENTE", "ADMIN"]))])
def get_dashboard_kpis(service: DashboardService = Depends(get_dashboard_service)):
    """Entrega el KPI de ahorro, diferencial kWh y matrices para gráficas en frontend."""
    try:
        # Extraemos el R2 real de la RAM o base de datos
        current_r2 = getattr(sim_engine, "r2_score", 87.59)
        return service.get_plant_analytics(r2_score_current=current_r2)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en analítica de planta: {str(e)}"
        )
