import logging
from typing import List, Optional
from app.repositories.ml_model_version_repository import MlModelVersionRepository
from app.models.ml_model_version import MlModelVersion, ModelStatus

logger = logging.getLogger(__name__)


class MlModelService:
    """Servicio de dominio para el control de versiones y auditoría de modelos XGBoost."""

    def __init__(self, repository: MlModelVersionRepository):
        self.repository = repository

    def get_active_model_version(self) -> Optional[MlModelVersion]:
        """Consulta cuál es el modelo Champion operativo actual en la base de datos."""
        return self.repository.get_champion_model()

    def get_model_history(self) -> List[dict]:
        """Formatea el historial de modelos para alimentar la tabla en la pantalla de Next.js."""
        models = self.repository.get_all_versions()
        history_list = []

        for m in models:
            history_list.append(
                {
                    "id": m.id,
                    "version_tag": m.version_tag,
                    "model_path": m.model_path,
                    "r2_score": (
                        round(float(m.r2_score), 2) if m.r2_score is not None else 0.0
                    ),
                    "rmse": round(float(m.rmse), 6) if m.rmse is not None else 0.0,
                    "batch_id": str(m.batch_id) if m.batch_id else "STATIC_BASE_MODEL",
                    "trained_at": (
                        m.trained_at.strftime("%Y-%m-%d %H:%M:%S")
                        if m.trained_at
                        else "N/A"
                    ),
                    "status": (
                        m.status.value if hasattr(m.status, "value") else str(m.status)
                    ),
                }
            )

        return history_list

    def register_new_version(
        self,
        version_tag: str,
        model_path: str,
        r2_score: float,
        rmse: float,
        batch_id=None,
        status: str = "ACTIVE",
        feature_importance: Optional[list] = None,
    ) -> MlModelVersion:
        """Registra una nueva inferencia. Si es ACTIVE, promueve a Champion archivando los anteriores."""
        logger.info(
            f"🚀 [MlModelService] Registrando nueva versión de IA en BD: {version_tag}"
        )

        enum_status = (
            ModelStatus.ACTIVE if status.upper() == "ACTIVE" else ModelStatus.ARCHIVED
        )

        payload = {
            "version_tag": version_tag,
            "model_path": model_path,
            "r2_score": r2_score,
            "rmse": rmse,
            "batch_id": batch_id,
            "status": enum_status,
            "feature_importance": feature_importance,
        }

        # 1. Primero creamos el registro en la base de datos
        new_model = self.repository.create(payload)
        logger.info(
            f"✨ [MlModelService] Modelo {version_tag} persistido con ID={new_model.id}."
        )

        # 2. Si se solicitó como ACTIVO, invocamos tu método optimizado para promoverlo a Champion
        if status.upper() == "ACTIVE":
            self.repository.set_new_champion(version_id=new_model.id)
            logger.info(
                f"🏆 [MlModelService] El modelo ID={new_model.id} es el nuevo Champion en producción."
            )

        return new_model
