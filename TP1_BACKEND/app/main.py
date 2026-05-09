# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import users # Importamos nuestro router
from app.core.database import Base, engine # Importamos la config de DB
import app.models.users_model
from app.api.routers import users, auth, ml, optimization, data, gmp, audit
from app.tasks.scheduler import start_scheduler

# Esto crea las tablas en la BD automáticamente al iniciar (solo para desarrollo)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 2. Configurar los orígenes permitidos ---
origins = [
    "http://localhost:3000",
    "http://192.168.0.100:3000", 
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],
)
# ---------------------------------------------

# Aquí "enchufamos" el router de usuarios
# app.include_router(plc.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(ml.router)
app.include_router(gmp.router)
app.include_router(audit.router)
# app.include_router(optimization.router)

@app.get("/")
def root():
    return {"mensaje": "¡Hola desde FastAPI!"}


# @app.on_event("startup")
# async def on_startup():
#     await start_scheduler()
