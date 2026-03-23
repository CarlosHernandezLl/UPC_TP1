# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Define la variable con el mismo nombre que en el .env
    DATABASE_URL: str
    
    SECRET_KEY: str = "Desarrollo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"  # Le indicamos dónde buscar

# Instanciamos la clase para usarla en el resto de la app
settings = Settings()