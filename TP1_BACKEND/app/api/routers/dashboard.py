from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import check_role

from app.services.dashboard_service import DashboardService

# 🚀 IMPORTAMOS LOS REPOSITORIOS
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.hvac_repository import HvacRepository

from app.repositories.ml_model_version_repository import MlModelVersionRepository

router = APIRouter(prefix="/dashboard", tags=["Analítica & BI"])

def get_dashboard_service(db: Session = Depends(get_db)) -> DashboardService:
    sim_repo = SimulationRepository(db)
    hvac_repo = HvacRepository(db)
    model_repo = MlModelVersionRepository(db)
    return DashboardService(
        sim_repo=sim_repo, hvac_repo=hvac_repo, model_repo=model_repo
    )


@router.get("/metrics", dependencies=[Depends(check_role(["GERENTE", "SUPERVISOR", "ADMIN"]))])
def get_dashboard_kpis(
    request: Request, service: DashboardService = Depends(get_dashboard_service)
):
    """Entrega el KPI de ahorro, diferencial kWh y matrices para gráficas en frontend."""
    try:
        # Fallback: R² en RAM del motor compartido (el Champion en BD tiene prioridad)
        engine = getattr(request.app.state, "simulator_engine", None)
        ram_r2 = getattr(engine, "r2_score", None)
        return service.get_plant_analytics(r2_score_current=ram_r2)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error en analítica de planta: {str(e)}"
        )
