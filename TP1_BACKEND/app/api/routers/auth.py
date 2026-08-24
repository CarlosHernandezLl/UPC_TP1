from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

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


@router.post("/register-first-user")
def register_initial(service: AuthService = Depends(get_auth_service)):
    return service.register_initial_admin()
