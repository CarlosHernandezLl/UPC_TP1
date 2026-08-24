from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.models.data_ingestion_log import DataIngestionLog

class DataIngestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, log_data: dict) -> DataIngestionLog:
        try:
            db_obj = DataIngestionLog(**log_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get_latest_sync(self) -> DataIngestionLog | None:
        return (
            self.db.query(DataIngestionLog)
            .order_by(DataIngestionLog.ingested_at.desc())
            .first()
        )

    def get_all_history(self) -> list[DataIngestionLog]:
        """Retorna el historial completo para la pantalla del frontend."""
        return (
            self.db.query(DataIngestionLog)
            .order_by(DataIngestionLog.ingested_at.desc())
            .all()
        )