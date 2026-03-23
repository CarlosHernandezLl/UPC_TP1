from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate # Asumiendo que crearás este esquema en schemas/

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str):
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_all_users(self):
        return self.db.query(User).all()

    def create(self, user_in: UserCreate, hashed_password: str):
        db_user = User(
            nombre=user_in.nombre,
            email=user_in.email,
            password=hashed_password,
            role=user_in.role
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user