from sqlalchemy.orm import Session
from app.models.users_model import User
from app.schemas.user_schema import UserCreate # Asumiendo que crearás este esquema en schemas/

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()
    
    def get_all_users(self):
        return self.db.query(User).all()

    def create(self, user_in: UserCreate, hashed_password: str):
        db_user = User(
            username=user_in.username,
            hashed_password = hashed_password,
            full_name = user_in.full_name,
            role= user_in.role,
            is_active = True
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, update_data: dict):
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if db_user:
            for key, value in update_data.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
        return db_user
    
    def delete(self, user_id: int):
        db_user = self.db.query(User).filter(User.id == user_id).first()
        if db_user:
            # self.db.delete(db_user)
            db_user.is_active = False
            self.db.commit()
            self.db.refresh(db_user)
        return db_user