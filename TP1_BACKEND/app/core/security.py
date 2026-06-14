from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    # 1. Convertir la contraseña de texto plano (str) a bytes
    password_bytes = password.encode('utf-8')
    
    # 2. Generar la sal (salt) y encriptar la contraseña
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # 3. Decodificar de nuevo a un string UTF-8 para guardarlo en la base de datos (VARCHAR/TEXT)
    return hashed_bytes.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Convertir tanto la contraseña ingresada como el hash guardado a bytes para compararlos
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)