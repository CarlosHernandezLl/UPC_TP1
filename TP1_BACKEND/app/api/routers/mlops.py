from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user, check_role

# 🚀 IMPORTACIÓN AGRUPADA: Servicios
from app.services.ml_training_service import MLTrainingService
from app.services.ml_model_service import MlModelService
from app.services.data_service import DataService
from app.services.audit_service import AuditService

# 🚀 IMPORTACIÓN AGRUPADA: Repositorios
from app.repositories.hvac_repository import HvacRepository
from app.repositories.data_ingestion_repository import DataIngestionRepository
from app.repositories.ml_model_version_repository import MlModelVersionRepository
from app.repositories.audit_repository import AuditRepository

from app.ml_engine.simulator_engine import SimulatorEngine

router = APIRouter(prefix="/mlops", tags=["MLOps & Model Registry"])

# Instancia única en RAM compartida del motor XGBoost (12 Variables)
sim_engine = SimulatorEngine()


# 🎯 PROVEEDOR 1: El especialista en Base de Datos e Historial (Para la UI)
def get_ml_model_service(db: Session = Depends(get_db)) -> MlModelService:
    model_repo = MlModelVersionRepository(db)
    return MlModelService(model_repo)


# 🎯 PROVEEDOR 2: El especialista Científico / Matemático (Para reentrenar)
def get_ml_training_service(db: Session = Depends(get_db)) -> MLTrainingService:
    # 1. Instanciamos los repositorios base
    hvac_repo = HvacRepository(db)
    ingestion_repo = DataIngestionRepository(db)
    model_repo = MlModelVersionRepository(db)
    audit_repo = AuditRepository(db)

    # 2. Instanciamos los servicios hermanos
    data_service = DataService(hvac_repo, ingestion_repo)
    model_service = MlModelService(model_repo)
    audit_service = AuditService(audit_repo)

    # 3. Inyectamos todo en el motor MLOps junto con la instancia en RAM
    return MLTrainingService(
        data_service=data_service,
        model_service=model_service,
        audit_service=audit_service,
        sim_engine=sim_engine,
    )


# =================================================================
# 1. ENDPOINT DE MÉTRICAS (Para las tarjetas superiores de la pantalla)
# =================================================================
@router.get(
    "/metrics", dependencies=[Depends(check_role(["SUPERVISOR", "AUDITOR", "ADMIN"]))]
)
def get_model_metrics(service: MLTrainingService = Depends(get_ml_training_service)):
    """Retorna las métricas reales del modelo Champion actual sin inventar números fantasma."""
    return service.get_active_model_metrics()


# =================================================================
# 2. ENDPOINT DE HISTORIAL (Para la tabla de reentrenamientos en Next.js)
# =================================================================
@router.get(
    "/history", dependencies=[Depends(check_role(["SUPERVISOR", "AUDITOR", "ADMIN"]))]
)
def get_retraining_history(
    model_service: MlModelService = Depends(get_ml_model_service),
):
    """Retorna el listado completo de todas las versiones de IA para la tabla de auditoría web."""
    try:
        return {
            "status": "success",
            "data": model_service.get_model_history(),
            "total_models": len(model_service.get_model_history()),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al leer el historial del Model Registry: {str(e)}",
        )


# =================================================================
# 3. ENDPOINT DE REENTRENAMIENTO (Disparado por el botón 'Reentrenar Ahora')
# =================================================================
@router.post("/retrain", dependencies=[Depends(check_role(["ADMIN"]))])
def trigger_retraining_pipeline(
    service: MLTrainingService = Depends(get_ml_training_service),
    current_user: any = Depends(get_current_user),
):
    """Dispara el pipeline científico: extracción, filtro SSD de tesis, rampa sintética y promoción GxP."""
    try:
        # Ejecuta la matemática y, si el R² > 70%, el propio servicio llama a MlModelService para guardar
        resultado = service.execute_retraining_pipeline(user_id=current_user.id)

        if resultado.get("status") in ["error", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=resultado.get("message") or resultado.get("reason"),
            )
        return resultado

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo crítico en el pipeline MLOps: {str(e)}",
        )
