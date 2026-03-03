import time 
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
import requests 
from typing import Optional
from datetime import datetime

# --- Importaciones de tu Base de Datos y Modelos ---
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.plc import DataPLC # 👈 Importamos el nuevo modelo que creamos

from app.core.socket_manager import manager
from app.core.security import get_current_user
from app.models.user import User


router = APIRouter(prefix="/plc", tags=["plc"])

# Esquema para recibir el dato desde Next.js
class PLCSendData(BaseModel):
    dato: float

last_nodered_heartbeat: float = 0.0
last_plc_data: float = 0.0

@router.post("/heartbeat")
async def receive_heartbeat():
    global last_nodered_heartbeat
    last_nodered_heartbeat = time.time()
    return {"ok": True}

@router.get("/status")
def get_plc_status():
    global last_nodered_heartbeat
    global last_plc_data
    
    now = time.time()
    nodered_elapsed = now - last_nodered_heartbeat
    plc_elapsed = now - last_plc_data
    
    return {
        "node_red_connected": nodered_elapsed < 15,
        "plc_connected": plc_elapsed < 15
    }

# --- NUEVO: HISTORIAL DE TENDENCIAS (Lectura de BD) ---
@router.get("/history")
def get_plc_history(
    start: Optional[datetime] = Query(None),
    end: Optional[datetime] = Query(None),
    db: Session = Depends(get_db), # 👈 Inyectamos la conexión a la BD
    current_user: User = Depends(get_current_user) # 👈 Protegemos la ruta
):
    query = db.query(DataPLC)
    
    # Aplicamos los filtros de fecha si Next.js los envía
    if start:
        query = query.filter(DataPLC.fecha >= start)
    if end:
        query = query.filter(DataPLC.fecha <= end)
        
    # Ordenamos por fecha y limitamos a 1000 registros para rendimiento
    records = query.order_by(DataPLC.fecha.asc()).limit(1000).all()
    
    # Formateamos la respuesta para Recharts en Next.js
    return [
        {
            "id": r.id, 
            "presion": float(r.dato_real), 
            "fecha": r.fecha.isoformat() 
        } 
        for r in records
    ]


# --- WEBSOCKET (Lectura en Tiempo Real) ---
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            global last_plc_data
            last_plc_data = time.time()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# --- ESCRITURA (Enviar al PLC) ---
@router.post("/write")
def write_to_plc(data: PLCSendData, current_user: User = Depends(get_current_user)):
   
    print(f"El operador {current_user.nombre} está escribiendo el valor {data.dato}")
    
    node_red_url = "http://127.0.0.1:1880/enviarVar" 
    
    try:
        response = requests.post(node_red_url, json={"dato": data.dato})
        if response.status_code == 200:
            return {"mensaje": "Enviado a Node-RED correctamente"}
        else:
            raise HTTPException(status_code=500, detail="Error en Node-RED")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))