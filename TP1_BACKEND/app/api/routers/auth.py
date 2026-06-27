from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.schemas.user_schema import UserCreate
from app.core.database import get_db
from app.models.users_model import User, UserRole
from app.schemas.user_schema import UserCreate
from app.core.security import verify_password, create_access_token
from datetime import timedelta
import app.core.security as security
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
    ):
    
    auth_service = AuthService(db)
    result = auth_service.login_user(form_data.username, form_data.password)
    
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
        secure=False
    )
    
    return result


@router.post("/register-first-user")
def register_initial(db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    user_data = UserCreate(
        username="admin_hvac",
        password="AdminPassword123!",
        full_name="Carlos Hernandez",
        role=UserRole.ADMIN
    )

    return auth_service.register_user(user_data)