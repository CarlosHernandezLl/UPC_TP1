# app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Define la variable con el mismo nombre que en el .env
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"  # Le indicamos dónde buscar
        env_file_encoding = "utf-8"

# Instanciamos la clase para usarla en el resto de la app
settings = Settings()