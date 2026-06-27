from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.users_model import User
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings
from datetime import timedelta

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def login_user(self, username: str, password: str):
        # 1. Buscar usuario por email o username (según tu preferencia)
        user = self.db.query(User).filter(User.username == username).first()
        
        # 2. Validar existencia y password
        if not user or not verify_password(password, user.hashed_password):
            return None # El router se encarga de lanzar la 401
            
        # 3. Validar estado (US005)
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inhabilitado por administración"
            )
            
        # 4. Generar Token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_info": {
                "full_name": user.full_name,
                "role": user.role.value
            }
        }

    def register_user(self, user_data):
        # Verificar si ya existe
        existing = self.db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="El usuario ya existe")
            
        new_user = User(
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user