import httpx
import logging
from typing import Dict, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    def __init__(self):
        self.lat = settings.WEATHER_LAT
        self.lon = settings.WEATHER_LON
        self.api_key = settings.OPENWEATHER_API_KEY
        self.url = "https://api.openweathermap.org/data/2.5/weather"

    async def get_external_weather(self) -> Optional[Dict[str, float]]:
        if not self.api_key:
            logger.warning(
                "OPENWEATHER_API_KEY no configurada en .env. Se omitirá lectura en vivo."
            )
            return None

        params = {
            "lat": self.lat,
            "lon": self.lon,
            "appid": self.api_key,
            "units": "metric",
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.url, params=params, timeout=8.0)
                response.raise_for_status()
                data = response.json()

                weather_data = {
                    "outdoor_temp": float(data["main"]["temp"]),
                    "outdoor_rh": float(data["main"]["humidity"]),
                    "city": data.get("name", "Lima"),
                }

                logger.info(
                    f"Éxito API Clima: {weather_data['city']} | Temp: {weather_data['outdoor_temp']}°C | RH: {weather_data['outdoor_rh']}%"
                )
                return weather_data

            except httpx.HTTPError as e:
                logger.error(f"Error HTTP al contactar OpenWeather API: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"Error procesando JSON meteorológico: {str(e)}")
                return None
