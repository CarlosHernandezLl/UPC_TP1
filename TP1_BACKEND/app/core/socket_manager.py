from fastapi import WebSocket
from typing import List, Optional  # Importamos Optional

class ConnectionManager:
    def __init__(self):
        # Lista para guardar las conexiones activas
        self.active_connections: List[WebSocket] = []
        # MEMORIA: Aquí guardaremos el último dato que envió Node-RED
        self.last_message: Optional[str] = None 

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        # --- EL TRUCO MAGICO ---
        # Si ya tenemos un dato guardado en memoria, se lo enviamos 
        # al usuario nuevo INMEDIATAMENTE al conectarse.
        if self.last_message:
            try:
                await websocket.send_text(self.last_message)
            except Exception as e:
                print(f"Error enviando último estado: {e}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        # 1. Guardamos el mensaje en la "memoria" antes de enviarlo
        self.last_message = message 
        
        # 2. Envía el mensaje a TODOS los conectados
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                # Si falla una conexión (ej. usuario cerró pestaña)
                print(f"Error en broadcast: {e}")
                pass

manager = ConnectionManager()