from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Base de Datos
    DATABASE_URL: str

    # Seguridad y JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Inteligencia Artificial y Clima (Con valores por defecto seguros)
    GEMINI_API_KEY: Optional[str] = ""
    OPENWEATHER_API_KEY: Optional[str] = ""
    WEATHER_LAT: float = -12.046374  # Latitud Lima, Perú
    WEATHER_LON: float = -77.042793  # Longitud Lima, Perú

    # CORS para Producción
    FRONTEND_URL: str = "https://upc-tp-1-sigma.vercel.app"

    # Configuración estricta Pydantic V2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignora variables extra en el .env si no están declaradas aquí
    )


# Instancia única tipo Singleton para ser importada en el proyecto
settings = Settings()
