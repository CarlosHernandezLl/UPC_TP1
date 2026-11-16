import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.repositories.ml_model_version_repository import (
    MlModelVersionRepository,
)
from app.services.ml_model_service import MlModelService
from app.core.config import settings
from app.core.database import SessionLocal
from app.repositories.gmp_repository import GmpRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.ml_engine.simulator_engine import (
    simulator_engine_instance,
)  # la instancia real, no el módulo

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

log_path = os.path.join(os.path.dirname(__file__), "..", "logs", "app.log")
os.makedirs(os.path.dirname(log_path), exist_ok=True)

logging.basicConfig(
    # stdout para que Render/Docker muestren los errores; además se guarda en archivo
    handlers=[logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")],
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)

# El esquema lo gestiona Alembic: `alembic upgrade head` (ver entrypoint de Docker).


def _seed_initial_admin(db) -> None:
    """En una BD vacía, crea el administrador inicial si hay FIRST_ADMIN_PASSWORD."""
    if not settings.FIRST_ADMIN_PASSWORD:
        return
    try:
        AuthService(UserRepository(db)).register_initial_admin(GmpRepository(db))
        logger.info("[Startup] Administrador inicial creado.")
    except HTTPException:
        pass  # ya existen usuarios


def _resolve_model_path(stored_path: str) -> str | None:
    """Resuelve la ruta del modelo; si la guardada no existe (otro SO/contenedor),
    busca el mismo archivo dentro de saved_models/."""
    if os.path.exists(stored_path):
        return stored_path
    models_dir = os.path.join(os.path.dirname(__file__), "ml_engine", "saved_models")
    candidate = os.path.join(models_dir, os.path.basename(stored_path.replace("\\", "/")))
    return candidate if os.path.exists(candidate) else None


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _load_champion(model_service: MlModelService, champion) -> bool:
    """Carga el Champion en RAM: primero desde la BD (sobrevive a discos efímeros), si no desde el archivo.

    Si solo existe el archivo, se copia a la BD para que el modelo no vuelva a depender del disco.
    """
    engine = simulator_engine_instance
    blob = champion.model_blob
    if blob and engine.reload_model_from_json(blob, version_tag=champion.version_tag):
        return True

    path = _resolve_model_path(champion.model_path)
    if path and engine.reload_model_in_memory(
        path, version_tag=champion.version_tag, origin="archivo"
    ):
        if not blob:
            model_service.store_model_blob(champion.id, _read_text(path))
        return True
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    db = SessionLocal()
    try:
        _seed_initial_admin(db)
        repo = MlModelVersionRepository(db)
        model_service = MlModelService(repo)
        champion = model_service.get_active_model_version()

        if champion and _load_champion(model_service, champion):
            logger.info(f"[Startup] Champion {champion.version_tag} cargado ({simulator_engine_instance.loaded_origin}).")
        else:
            logger.error(
                "[Startup] No se pudo cargar el Champion (sin contenido en BD ni archivo); "
                "se usa el modelo base. Reentrene el modelo desde Entrenamiento IA."
            )
    except Exception as e:
        logger.error(
            f"❌ [Startup] Error al cargar Champion desde BD: {e}. Continuando con fallback estático."
        )
    finally:
        db.close()

    app.state.simulator_engine = (
        simulator_engine_instance  # 🎯 fuente única para toda la app
    )
    yield
    # --- Shutdown: nada que limpiar por ahora ---


app = FastAPI(
    title="HVAC AI Engine",
    description="Backend industrial GxP con Gemelo Digital y optimización energética mediante XGBoost",
    version="2.0.0",
    lifespan=lifespan,
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
