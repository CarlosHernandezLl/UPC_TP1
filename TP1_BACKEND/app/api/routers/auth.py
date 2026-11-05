from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.repositories.gmp_repository import GmpRepository
from app.repositories.revoked_token_repository import RevokedTokenRepository
from app.api.deps import oauth2_scheme, get_current_user, get_audit_service
from app.core.config import settings
from app.models.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["auth"])

def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

def get_auth_service(user_repo: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repo)


@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
):
    result = service.login_user(
        username=form_data.username, password=form_data.password
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    response.set_cookie(
        key="scada_token",
        value=result["access_token"],
        httponly=False,
        max_age=3600,
        samesite="lax",
        secure=False,
    )

    return result


@router.post("/logout")
def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Revoca el token vigente: deja de ser válido en el servidor aunque no haya vencido."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")

    jti = payload.get("jti")
    if jti:
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        RevokedTokenRepository(db).revoke(jti, expires_at)

    audit_service.record_action(
        user_id=current_user.id, action="USER_LOGOUT", resource="AUTH", detail="Sesión cerrada por el usuario."
    )
    response.delete_cookie("scada_token")
    return {"status": "success"}


@router.post("/register-first-user")
def register_initial(
    service: AuthService = Depends(get_auth_service), db: Session = Depends(get_db)
):
    return service.register_initial_admin(GmpRepository(db))
