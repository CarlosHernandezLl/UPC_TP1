from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    # Base de Datos
    DATABASE_URL: str

    # Seguridad y JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Inteligencia Artificial (valor por defecto seguro)
    GEMINI_API_KEY: Optional[str] = ""

    # Administrador inicial (solo se crea si no existen usuarios)
    FIRST_ADMIN_USERNAME: str = "admin_hvac"
    FIRST_ADMIN_FULL_NAME: str = "Administrador de Planta"
    FIRST_ADMIN_PASSWORD: Optional[str] = ""

    # CORS para Producción
    FRONTEND_URL: str = "https://upc-tp-1-sigma.vercel.app"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Render entrega 'postgres://', que SQLAlchemy 2 no reconoce
        if v.startswith("postgres://"):
            return "postgresql://" + v[len("postgres://"):]
        return v

    # Configuración estricta Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora variables extra en el .env si no están declaradas aquí
    )


# Instancia única tipo Singleton para ser importada en el proyecto
settings = Settings()
