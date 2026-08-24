from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, check_role

# 🚀 IMPORTACIÓN AGRUPADA: Esquemas
from app.schemas.simulation_schema import (
    SimulationPredictRequest,
    SimulationLogRequest,
    SimulationPredictResponse,
)

# 🚀 IMPORTACIÓN AGRUPADA: Servicios del dominio
from app.services.simulation_service import SimulationService
from app.services.gmp_service import GmpService
from app.services.llm_service import LlmService
from app.services.audit_service import AuditService

# 🚀 IMPORTACIÓN AGRUPADA: Repositorios necesarios para ensamblar los servicios
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.gmp_repository import GmpRepository
from app.repositories.audit_repository import AuditRepository

from app.ml_engine.simulator_engine import SimulatorEngine

router = APIRouter(prefix="/simulation", tags=["Gemelo Digital HVAC"])

# Instancia en RAM compartida del motor XGBoost
sim_engine = SimulatorEngine()


# 🎯 PROVEEDOR CORREGIDO: Ensamblamos todo el árbol de dependencias que exige SimulationService
def get_simulation_service(db: Session = Depends(get_db)) -> SimulationService:
    # 1. Instanciamos repositorios
    sim_repo = SimulationRepository(db)
    gmp_repo = GmpRepository(db)
    audit_repo = AuditRepository(db)

    # 2. Instanciamos servicios de soporte
    audit_service = AuditService(audit_repo)
    gmp_service = GmpService(repository=gmp_repo, audit_service=audit_service)
    llm_service = LlmService()

    # 3. Inyectamos las 5 piezas exactas en el constructor del servicio principal
    return SimulationService(
        sim_repo=sim_repo,
        gmp_service=gmp_service,
        llm_service=llm_service,
        audit_service=audit_service,
        simulator_engine=sim_engine,
    )


@router.post(
    "/predict",
    response_model=SimulationPredictResponse,
    dependencies=[Depends(check_role(["SUPERVISOR", "ADMIN"]))],
)
def predict_hvac_power(
    payload: SimulationPredictRequest,  # 🎯 SOLO EXIGE VARIABLES CLIMÁTICAS
    service: SimulationService = Depends(get_simulation_service),
):
    """Devuelve la recomendación del Gemelo Digital y la justificación técnica de Gemini."""
    return service.predict_optimal_power(payload.model_dump())


@router.post(
    "/log-action",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_role(["SUPERVISOR", "ADMIN"]))],
)
def log_simulation_action(
    payload: SimulationLogRequest,  # 🎯 EXIGE TELEMETRÍA + DECISIÓN DEL OPERADOR
    service: SimulationService = Depends(get_simulation_service),
    current_user: any = Depends(get_current_user),
):
    """Guarda la decisión final del operador sobre la máquina UMA y genera auditoría GxP."""
    try:
        return service.register_operator_decision(
            user_id=current_user.id, sim_data=payload.model_dump()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar simulación: {str(e)}",
        )
