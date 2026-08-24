from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID  # 🚀 Importación del UUID nativo
from app.core.database import Base


class DataIngestionLog(Base):
    __tablename__ = "data_ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)

    # 🚀 LINAJE GxP: El puente de auditoría entre el evento web y las filas físicas en BD
    batch_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    ingested_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("America/Lima"))
    )
    data_range = Column(String(50), nullable=False)
    record_count = Column(Integer, nullable=False)
    status = Column(String(30), nullable=False)
