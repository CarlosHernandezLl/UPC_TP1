from sqlalchemy.orm import Session
from app.models.optimization_model import OptimizationLog
from app.schemas.optimization_schema import OptimizationLogCreate

class OptimizationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_log(self, user_id: int, log_in: OptimizationLogCreate) -> OptimizationLog:
        db_log = OptimizationLog(
            user_id=user_id,
            timestamp = log_in.time,
            temp_ext=log_in.temp_ext,
            hum_ext=log_in.hum_ext,
            temp_uma=log_in.temp_uma,
            hum_uma=log_in.hum_uma,
            hum_sala_actual=log_in.hum_sala_actual, 
            setpoint_humedad=log_in.setpoint_humedad,
            potencia_actual=log_in.potencia_actual,
            potencia_recomendada=log_in.potencia_recomendada,
            potencia_aplicada=log_in.potencia_aplicada,
            accion=log_in.accion,
            justificacion=log_in.justificacion
        )
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log