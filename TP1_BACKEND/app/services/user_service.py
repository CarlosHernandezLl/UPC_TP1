from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UserRepository(db)

    def get_all_users(self):
        return self.repository.get_all_users()

    def get_user_by_id(db: Session, user_id: int):
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, user: UserCreate):
        
        if self.repository.get_by_email(user.email):
            return None
        
        # 1. Hashear la contraseña antes de guardarla
        hashed_pwd = get_password_hash(user.password)
        
        return self.repository.create(user,hashed_pwd)

    def update_user(db: Session, user_id: int, user_update: UserUpdate):
        # Reutilizamos nuestra propia función para buscar
        user_db = get_user_by_id(db, user_id)
    
        if not user_db:
            return None # Retornamos None para que el Router decida qué error lanzar

        # Actualizar campos
        if user_update.nombre is not None:
            user_db.nombre = user_update.nombre
        if user_update.email is not None:
            user_db.email = user_update.email
        if user_update.activo is not None:
            user_db.activo = user_update.activo

        db.commit()
        db.refresh(user_db)
        return user_db

    def delete_user(db: Session, user_id: int):
        user_db = get_user_by_id(db, user_id)
        if user_db:
            db.delete(user_db)
            db.commit()
            return True
        return False