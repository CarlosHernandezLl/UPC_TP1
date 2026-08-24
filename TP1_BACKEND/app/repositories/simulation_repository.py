from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.simulation_log import SimulationLog


class SimulationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, user_id: int, sim_data: dict, model_version_id: int = None
    ) -> SimulationLog:
        """Registra la decisión operativa con protección transaccional (rollback)."""
        try:
            db_log = SimulationLog(
                user_id=user_id,
                model_version_id=model_version_id,
                outdoor_temp=sim_data["outdoor_temp"],
                outdoor_rh=sim_data["outdoor_rh"],
                ahu_temp=sim_data["ahu_temp"],
                ahu_rh=sim_data["ahu_rh"],
                current_room_rh=sim_data["current_room_rh"],
                target_setpoint=sim_data["target_setpoint"],
                current_power=sim_data["current_power"],
                recommended_power=sim_data["recommended_power"],
                applied_power=sim_data["applied_power"],
                action=sim_data["action"],
                justification=sim_data.get("justification"),
            )
            self.db.add(db_log)
            self.db.commit()
            self.db.refresh(db_log)
            return db_log
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get_by_user(self, user_id: int, limit: int = 50) -> list[SimulationLog]:
        """Obtiene las simulaciones ejecutadas por un operador específico."""
        return (
            self.db.query(SimulationLog)
            .filter(SimulationLog.user_id == user_id)
            .order_by(SimulationLog.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_recent_simulations(self, limit: int = 24) -> list[SimulationLog]:
        """
        🚀 NUEVO: Obtiene las últimas simulaciones de TODA LA PLANTA sin filtrar por usuario.
        Requerido por el DashboardService para graficar el área de consumo Real vs Ideal.
        """
        return (
            self.db.query(SimulationLog)
            .order_by(SimulationLog.timestamp.desc())
            .limit(limit)
            .all()
        )
