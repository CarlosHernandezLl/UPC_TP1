from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt # 👈 Solo dejamos esta importación de jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.repositories.audit_repository import AuditRepository
from app.schemas.audit import AuditLogCreate

import bcrypt

# Configuración de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración JWT (En producción, pon el SECRET_KEY en tu .env)
SECRET_KEY = "super_secreto_industrial_cambiar_en_produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 horas

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Esto le dice a FastAPI dónde está la ruta para obtener el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
# security = HTTPBearer()

# Esta es nuestra función "Guardián"
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Intentamos decodificar el token con nuestra clave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    # Buscamos que el usuario realmente exista en la base de datos
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    # Si todo está bien, devolvemos el usuario
    return user


def check_role(required_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.role not in required_roles:
            audit_repo = AuditRepository(db)
            audit_data = AuditLogCreate(
                user_id=current_user.id,
                action="ACCESO DENEGADO",
                module="SEGURIDAD",
                description=f"Intento de acceso a {required_roles} con rol {current_user.role}",
                payload={"role_actual": current_user.role, "roles_requeridos": required_roles}
            )

            audit_repo.create_log(audit_data)

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes para esta acción"
            )
        return current_user
    return role_checker