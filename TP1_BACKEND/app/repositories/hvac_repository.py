from sqlalchemy.orm import Session
from app.models.hvac import HVACReading
from app.schemas.hvac import HvacReadingCreate

class HvacRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_reading(self, reading_in: HvacReadingCreate) -> HvacReading:
        # Convertimos el esquema de Pydantic a un modelo de SQLAlchemy
        db_obj = HvacReading(**reading_in.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_latest(self, limit: int = 10):
        return self.db.query(HvacReading).order_by(HvacReading.timestamp.desc()).limit(limit).all()