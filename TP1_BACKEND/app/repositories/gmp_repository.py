from sqlalchemy.orm import Session
from app.models.gmp_model import GmpParameter

class GmpRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_current_parameters(self):
        # Retornamos la configuración activa (ID 1)
        return self.db.query(GmpParameter).first()

    def update_parameters(self, user_id: int, data: dict):
        params = self.db.query(GmpParameter).first()
        
        if not params:
            params = GmpParameter(**data, updated_by=user_id)
            self.db.add(params)
        else:
            for key, value in data.items():
                setattr(params, key, value)
            params.updated_by = user_id
            
        self.db.commit()
        self.db.refresh(params)
        return params