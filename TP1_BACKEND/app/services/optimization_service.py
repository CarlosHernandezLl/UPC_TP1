from sqlalchemy.orm import Session

class OptimizationService:
    def __init__(self, db: Session):
        self.db = db