# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import users # Importamos nuestro router
from app.core.database import Base, engine # Importamos la config de DB
import app.models.user
from app.api.routers import users, plc, auth
from app.tasks.scheduler import start_scheduler


# Esto crea las tablas en la BD automáticamente al iniciar (solo para desarrollo)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 2. Configurar los orígenes permitidos ---
origins = [
    "http://localhost:3000", # La casa de Next.js
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
app.include_router(users.router)
app.include_router(plc.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"mensaje": "¡Hola desde FastAPI!"}

@app.on_event("startup")
async def on_startup():
    await start_scheduler()