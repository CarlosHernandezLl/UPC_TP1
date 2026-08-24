from datetime import timedelta
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.config import settings


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def login_user(self, username: str, password: str) -> dict:
        user = self.user_repository.get_by_username(username)

        if not user or not verify_password(password, user.hashed_password):
            return None  # El controlador emitirá el HTTP 401

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inhabilitado por administración o seguridad GxP",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": user.username, "role": user.role.value},
            expires_delta=access_token_expires,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_info": {"full_name": user.full_name, "role": user.role.value},
        }

    def register_user(self, user_data) -> dict:
        existing = self.user_repository.get_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=400, detail="El nombre de usuario ya está registrado."
            )

        hashed_pwd = get_password_hash(user_data.password)
        new_user = self.user_repository.create(user_data.model_dump(), hashed_pwd)
        return new_user
