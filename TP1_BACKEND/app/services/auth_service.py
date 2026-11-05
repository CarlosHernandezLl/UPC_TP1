from datetime import timedelta
from fastapi import HTTPException, status
from app.repositories.user_repository import UserRepository
from app.repositories.gmp_repository import GmpRepository
from app.models.user import UserRole
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

    def register_initial_admin(self, gmp_repository: GmpRepository) -> dict:
        """Crea el administrador inicial y los límites GMP por defecto en una BD vacía."""
        if self.user_repository.get_all(limit=1):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El sistema ya tiene usuarios registrados.",
            )
        if not settings.FIRST_ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Defina FIRST_ADMIN_PASSWORD para crear el administrador inicial.",
            )

        admin = self.user_repository.create(
            {
                "username": settings.FIRST_ADMIN_USERNAME,
                "full_name": settings.FIRST_ADMIN_FULL_NAME,
                "role": UserRole.ADMIN,
            },
            get_password_hash(settings.FIRST_ADMIN_PASSWORD),
        )
        if not gmp_repository.get_current_parameters():
            gmp_repository.update_parameters(
                admin.id,
                {"min_hum_limit": 40.0, "max_hum_limit": 55.0, "default_setpoint": 49.0},
            )
        return {"status": "success", "username": admin.username}

    def register_user(self, user_data) -> dict:
        existing = self.user_repository.get_by_username(user_data.username)
        if existing:
            raise HTTPException(
                status_code=400, detail="El nombre de usuario ya está registrado."
            )

        hashed_pwd = get_password_hash(user_data.password)
        new_user = self.user_repository.create(user_data.model_dump(), hashed_pwd)
        return new_user
