import httpx
import logging
from typing import Dict, Optional
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.config import settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
lat, lon = -12.046374, -77.042793 
API_KEY = '7366c6055fe1a7ba1b0768982f8ec41a'

async def fetch_and_save_weather(db: Session):
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    
    
    params = {
        "lat": lat, "lon": lon, # Ajustar a tu ubicación
        "appid": API_KEY,
        "units": "metric",
        "exclude": "minutely,hourly,daily,alerts"
    }
    

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params = params)
            response.raise_for_status()
            data = response.json()
            print("Clima Actual", data)
            
            temp = data["main"]["temp"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            wind_speed = data["wind"]["speed"]
            city = data["name"]
        
            return True
        except Exception as e:
            print(f"Error en ingesta de clima: {e}")
            return False


async def get_external_weather() -> Optional[Dict[str, float]]:
    # Coordenadas de ejemplo (Lima, Perú)    
    # URL específica para One Call 2.5
    url = "https://api.openweathermap.org/data/2.5/weather" 
       
    params = {
        "lat": lat,
        "lon": lon,
        "appid": API_KEY,
        "units": "metric",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            
            data = response.json()
            
            # Mapeo directo a tus variables del dataset
            # current = data["current"]
            weather_data = {
                "temperatura_exterior": float(data["main"]["temp"]),
                "humedad_exterior": float(data["main"]["humidity"])
            }
            
            logger.info(f"Éxito INF01 - Clima actual: {weather_data}")
            return weather_data

        except Exception as e:
            logger.error(f"Error en One Call API 3.0: {str(e)}")
            return None