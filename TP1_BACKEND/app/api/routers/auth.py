from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.users_model import User
from app.core.security import verify_password, create_access_token
from datetime import timedelta
import app.core.security as security
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    result = auth_service.login_user(form_data.username, form_data.password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.post("/register-first-user")
def register_initial(db: Session = Depends(get_db)):
    # Solo para inicializar la base de datos la primera vez
    from app.models.users import UserRole
    auth_service = AuthService(db)
    # Datos de ejemplo
    class FakeSchema:
        username = "admin_hvac"
        password = "AdminPassword123!"
        full_name = "Carlos Hernandez"
        role = UserRole.ADMIN
        
    return auth_service.register_user(FakeSchema())