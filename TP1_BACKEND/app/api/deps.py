# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.audit_model import AuditTrail 
from app.models.users_model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def check_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.role.value not in required_roles:
            # US019: Auditoría de acceso denegado (Crucial para Pharma)
            new_audit = AuditTrail(
                user_id=current_user.id,
                action_type="ACCESO_DENEGADO",
                description=f"Intento de entrar a módulos {required_roles} con rol {current_user.role.value}",
                ip_address="0.0.0.0" # Puedes capturarla del request si quieres
            )
            db.add(new_audit)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para esta acción"
            )
        return current_user
    return role_checker