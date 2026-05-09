import asyncio
import logging
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.database import SessionLocal
from app.services.weather_service import fetch_and_save_weather

# app = FastAPI()
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

async def sync_external_weather():
    """Tarea para clima real"""
    logger.info("Iniciando sincronización de clima externo...")
    db = SessionLocal()
    try:
        await fetch_and_save_weather(db)
        logger.info("Clima externo sincronizado con éxito")
    except Exception as e:
        logger.error(f"Error sincronizando clima: {e}")
    finally: 
        db.close()



async def start_scheduler():
    """Punto de entrada principal"""
    #1. Ejecutar carga inicial
    #await run_initial_load()
    
    #2. Programar tareas concurrentes (Datos reales)
    # Clima: Cada 10 minutos (600 segundos) para no quemar la API
    scheduler.add_job(sync_external_weather, 'interval', minutes=1, id = "weather_job")
    
    # PLC: Cada 30 segundos (cuando tengas la conexión real)
    # scheduler.add_job(sync_plc_data, 'interval', seconds = 30, id= "plc_job")
    
    #3. Iniciar el scheduler
    scheduler.start()
    logger.info("Scheduler iniciado y tareas programadas")
    




# Programar tareas (ejemplo: cada 5 minutos)
#scheduler.add_job(sync_external_weather, 'interval', minutes=5)
#scheduler.add_job(sync_plc_data, 'interval', seconds=30) # El PLC es más crítico
#scheduler.start()


   