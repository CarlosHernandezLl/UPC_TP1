# app/api/deps.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.ml_engine.simulator_engine import SimulatorEngine
from app.core.config import settings
from app.core.database import get_db

# 🚀 1. IMPORTACIONES ÚNICAMENTE DE SERVICIOS Y MODELOS: Cero Repositorios en la lógica web
from app.models.user import User
from app.services.user_service import UserService
from app.services.audit_service import AuditService

# (Importación interna solo para el inyector de dependencias de FastAPI)
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --- PROVEEDORES DE CAPA DE NEGOCIO (Dependency Injection Providers) ---
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    userRepository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(userRepository)


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    return AuditService(AuditRepository(db))


# -----------------------------------------------------------------------


def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(
        get_user_service
    ),  # 🚀 2. INYECTAMOS EL SERVICIO
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 🚀 3. CONSUMO PURO DEL SERVICIO: El interceptor ignora cómo y dónde se busca en BD
    user = user_service.get_by_username(username)

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def check_role(required_roles: list[str]):
    def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        audit_service: AuditService = Depends(
            get_audit_service
        ),  # 🚀 4. INYECTAMOS EL SERVICIO DE AUDITORÍA
    ) -> User:
        user_role = (
            current_user.role.value
            if hasattr(current_user.role, "value")
            else str(current_user.role)
        )

        if user_role not in required_roles and user_role != "ADMIN":

            client_ip = request.client.host if request.client else "UNKNOWN_IP"

            # 🚀 5. LLAMADA AL SERVICIO: Trazabilidad GxP delegada al dominio correspondiente
            audit_service.record_action(
                user_id=current_user.id,
                action="ACCESS_DENIED",
                resource="ACCESS_CONTROL",
                detail=f"Unauthorized attempt to access module requiring {required_roles} with role '{user_role}'. IP: {client_ip}",
            )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para realizar esta acción.",
            )

        return current_user

    return role_checker


def get_simulator_engine(request: Request) -> SimulatorEngine:
    return request.app.state.simulator_engine
