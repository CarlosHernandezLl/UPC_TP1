from sqlalchemy.orm import Session
from app.models.gmp_parameter import GmpParameter

class GmpRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_current_parameters(self) -> GmpParameter | None:
        return self.db.query(GmpParameter).first()

    def update_parameters(self, user_id: int, data: dict) -> GmpParameter:
        params = self.get_current_parameters()
        
        if not params:
            params = GmpParameter(**data, updated_by=user_id)
            self.db.add(params)
        else:
            for key, value in data.items():
                if hasattr(params, key):
                    setattr(params, key, value)
            params.updated_by = user_id
            
        self.db.commit()
        self.db.refresh(params)
        return params