from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.ml_model_version import MlModelVersion, ModelStatus


class MlModelVersionRepository:
    """Repositorio relacional para la tabla ml_model_versions (Model Registry GxP)."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, version_data: dict) -> MlModelVersion:
        """Inserta el registro inmutable de una nueva versión de IA entrenada."""
        try:
            db_obj = MlModelVersion(**version_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get_champion_model(self) -> Optional[MlModelVersion]:
        """Obtiene el modelo actualmente activo en producción para realizar inferencias."""
        return (
            self.db.query(MlModelVersion)
            .filter(MlModelVersion.status == ModelStatus.ACTIVE)
            .order_by(MlModelVersion.trained_at.desc())
            .first()
        )

    def get_all_versions(self) -> List[MlModelVersion]:
        """🚀 OBLIGATORIO PARA EL FRONTEND: Retorna el historial completo ordenado para la tabla web."""
        return (
            self.db.query(MlModelVersion)
            .order_by(MlModelVersion.trained_at.desc())
            .all()
        )

    def set_new_champion(self, version_id: int) -> Optional[MlModelVersion]:
        """Pasa todos los modelos a ARCHIVED en un solo query SQL y activa únicamente el nuevo candidato."""
        try:
            # 🎯 TU ACERTIJO SQL: Optimización masiva directa en el motor de base de datos
            self.db.query(MlModelVersion).filter(
                MlModelVersion.status == ModelStatus.ACTIVE
            ).update({"status": ModelStatus.ARCHIVED})

            new_champion = (
                self.db.query(MlModelVersion)
                .filter(MlModelVersion.id == version_id)
                .first()
            )
            if new_champion:
                new_champion.status = ModelStatus.ACTIVE
                self.db.commit()
                self.db.refresh(new_champion)
            return new_champion
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
