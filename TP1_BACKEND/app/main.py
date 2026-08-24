import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine

# 1. IMPORTACIÓN DE MODELOS (Obligatorio para que SQLAlchemy registre todas las tablas)
# Al importarlos sin el prefijo "TP1_BACKEND.", evitamos caídas en Docker/Render y aseguramos
# que Base.metadata.create_all() construya las 8 tablas de nuestra arquitectura GxP.
import app.models.user
import app.models.hvac_historical_data
import app.models.ml_model_version
import app.models.simulation_log
import app.models.audit_trail
import app.models.data_ingestion_log
import app.models.energy_pricing
import app.models.gmp_parameter

# 2. IMPORTACIÓN DE ENRUTADORES (Reemplazamos el antiguo 'ai' por los 3 nuevos dominios limpios)
from app.api.routers import (
    users,
    auth,
    data,
    gmp,
    audit,
    simulation,
    mlops,
    dashboard,
)

logging.basicConfig(
    filename="logs/app.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# Sincronización automática de esquema relacional en la base de datos
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✨ [SQLAlchemy] Tablas GxP verificadas y sincronizadas exitosamente.")
except Exception as e:
    logger.error(
        f"❌ [SQLAlchemy] Error al inicializar tablas en la base de datos: {e}"
    )

app = FastAPI(
    title="HVAC AI Engine",
    description="Backend industrial GxP con Gemelo Digital y optimización energética mediante XGBoost",
    version="2.0.0",  # Subimos a v2.0 para reflejar la refactorización arquitectónica (DDD)
)

# --- 3. Configuración Dinámica de CORS para Producción y Desarrollo ---
origins = [
    "http://localhost:3000",
    "http://192.168.0.100:3000",
]

# Inyección limpia de la URL de producción (Vercel o variable de entorno de Render)
frontend_production_url = os.getenv("FRONTEND_URL", "https://upc-tp-1-sigma.vercel.app")
if frontend_production_url not in origins:
    origins.append(frontend_production_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------------------------------------

# 4. INYECCIÓN DE ENDPOINTS EN EL CICLO DE VIDA DE FASTAPI
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(data.router)
app.include_router(gmp.router)
app.include_router(audit.router)
app.include_router(simulation.router)
app.include_router(mlops.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "Online",
        "environment": "Production GxP",
        "context": "Pharmaceutical HVAC Digital Twin Backend",
        "architecture": "DDD (Domain-Driven Design)",
        "engine": "XGBoost Active",
    }
