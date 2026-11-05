from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.hvac_historical_data import HvacHistoricalData


class HvacRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, reading_data: dict) -> HvacHistoricalData:
        db_obj = HvacHistoricalData(**reading_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_latest(self, limit: int = 100) -> list[HvacHistoricalData]:
        return (
            self.db.query(HvacHistoricalData)
            .order_by(HvacHistoricalData.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_power_humidity_series(self) -> list[tuple]:
        """Serie histórica completa (ts, potencia, humedad de sala), solo las columnas necesarias."""
        return (
            self.db.query(
                HvacHistoricalData.timestamp,
                HvacHistoricalData.dryer_power,
                HvacHistoricalData.room_w,
            )
            .filter(
                HvacHistoricalData.dryer_power.isnot(None),
                HvacHistoricalData.room_w.isnot(None),
            )
            .order_by(HvacHistoricalData.timestamp)
            .all()
        )

    def get_by_batch_id(self, batch_id: str) -> list[HvacHistoricalData]:
        """Extrae exclusivamente los registros del lote especificado para el re-entrenamiento MLOps"""
        return (
            self.db.query(HvacHistoricalData)
            .filter(HvacHistoricalData.batch_id == batch_id)
            .all()
        )

    def bulk_save(self, records: list[HvacHistoricalData]) -> int:
        """Inserta miles de registros en una sola transacción optimizada (Fast-Path)."""
        try:
            self.db.bulk_save_objects(records)
            self.db.commit()
            return len(records)
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
