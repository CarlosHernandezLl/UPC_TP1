# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine 
import app.models.users_model

# Importación unificada de routers (Limpia y sin duplicados para tu informe)
from app.api.routers import users, auth, data, gmp, audit, ai

# Esto crea las tablas en la BD automáticamente (Supabase lo asimilará al arrancar)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SCADA HVAC AI Engine",
    description="Backend industrial con optimización energética mediante XGBoost",
    version="1.0.0"
)

# --- 2. Configuración Dinámica de CORS para Producción ---
# Mantenemos los accesos locales para tus pruebas en casa
origins = [
    "http://localhost:3000",
    "http://192.168.0.100:3000",
]

# 💡 TRUCO DE INGENIERÍA: Si tienes tu URL de Vercel, la inyectamos dinámicamente.
# Puedes agregar una variable llamada FRONTEND_URL en el panel de Render
# o simplemente reemplazar el texto de abajo por tu URL de Vercel directamente.
frontend_production_url = os.getenv("FRONTEND_URL")
if frontend_production_url:
    origins.append(frontend_production_url)
else:
    # Si no quieres usar variables de entorno en Render para esto, 
    # simplemente pega tu URL de Vercel aquí abajo directamente:
    origins.append("https://upc-tp-1-sigma.vercel.app/") 

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # ⚠️ OBLIGATORIO: Para que el navegador permita guardar las cookies JWT en producción
    allow_methods=["*"], 
    allow_headers=["*"],
)
# ---------------------------------------------------------

# Inyección ordenada de endpoints en el ciclo de vida de FastAPI
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(data.router)
app.include_router(gmp.router)
app.include_router(audit.router)
app.include_router(ai.router)

@app.get("/")
def root():
    return {
        "status": "Online",
        "context": "GXP Pharmaceutical HVAC Digital Twin Backend",
        "engine": "XGBoost Active"
    }