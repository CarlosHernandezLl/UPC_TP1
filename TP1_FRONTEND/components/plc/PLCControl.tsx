// src/components/plc/PLCControl.tsx
"use client";

import { useState, useEffect, useRef } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const WS_URL = API_URL?.replace("http", "ws") + "/plc/ws";

export default function PLCControl() {
  const [plcData, setPlcData] = useState({
    presion: 0,
    temperatura: 0,
  });

  const ws = useRef<WebSocket | null>(null);

  // --- ESTADOS PARA EDICIÓN EN LÍNEA ---
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState("");
  // useRef para poder enfocar (focus) el input automáticamente al hacer clic
  const inputRef = useRef<HTMLInputElement>(null); 

  // 1. Conexión WebSocket (Lectura)
  useEffect(() => {
    ws.current = new WebSocket(WS_URL);

    // Eliminamos ws.current.onopen y ws.current.onclose ya que no actualizamos el estado
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        // Solo actualizamos el estado si NO estamos escribiendo
        // Esto evita que un dato viejo del PLC sobreescriba lo que el usuario está tecleando
        setPlcData((prevData) => ({
           presion: Number(data.presion) || prevData.presion,
           temperatura: Number(data.temperatura) || prevData.temperatura
        }));

      } catch (e) {
        console.error("Error parseando WS:", e);
      }
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  // Autofocus: Cuando se activa la edición, enfocar el input
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  // 2. Función para escribir (Escritura)
  const handleSend = async (valueToSend: number) => {
    try {
      const getCookie = (name: string) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop()?.split(";").shift();
        return null;
      };

      const token = getCookie("scada_token");
      if (!token) {
        alert("Tu sesión ha expirado, por favor vuelve a ingresar.");
        return;
      }

      // Actualización "Optimista": Cambiamos el número en pantalla inmediatamente
      // para que el usuario sienta que fue instantáneo.
      setPlcData(prev => ({ ...prev, presion: valueToSend }));
      setIsEditing(false); // Cerramos el modo edición

      // Enviamos el dato al backend en silencio (sin alertas)
      const res = await fetch(`${API_URL}/plc/write`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ dato: valueToSend }),
      });

      if (res.status === 401) {
        alert("No tienes permiso para escribir en el PLC.");
        // Si no tenía permiso, revertimos el cambio (opcional)
      } else if (!res.ok) {
        console.error("Error al enviar dato al PLC");
      }
    } catch (error) {
      console.error(error);
    }
  };

  // 3. Manejadores de Eventos del Input
  const startEditing = () => {
    setEditValue(plcData.presion.toString());
    setIsEditing(true);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      const numValue = parseFloat(editValue);
      if (!isNaN(numValue)) {
        handleSend(numValue);
      } else {
        setIsEditing(false); // Cancela si escribió letras o vacío
      }
    }
    if (e.key === "Escape") {
      setIsEditing(false); // Cancela si presiona Esc
    }
  };

  return (
    <div className="p-6 bg-gray-800 rounded-lg border border-gray-700 text-white w-full max-w-md mt-8">
      <h2 className="text-2xl font-bold mb-4 flex justify-between items-center">
        Monitor PLC (S7-1200)
        {/* Eliminado el span de estado */}
      </h2>

      <div className="grid grid-cols-2 gap-4 mb-2">
        {/* Tarjeta Variable 1: PRESIÓN (Interactiva) */}
        <div 
          className="text-center p-4 bg-gray-900 rounded border border-blue-500 hover:bg-gray-800 hover:border-blue-400 cursor-pointer transition-colors group relative"
          onClick={!isEditing ? startEditing : undefined}
          title="Haz clic para modificar"
        >
          <p className="text-gray-400 text-sm mb-1 group-hover:text-blue-300 transition-colors">Presión</p>
          
          <div className="h-10 flex items-center justify-center">
            {isEditing ? (
              <input
                ref={inputRef}
                type="number"
                step="0.1"
                className="w-24 text-center text-2xl font-mono font-bold text-blue-400 bg-gray-950 border border-blue-600 rounded outline-none ring-2 ring-blue-500/50"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                onKeyDown={handleKeyDown}
                onBlur={() => setIsEditing(false)} // Si hace clic fuera, cancela
              />
            ) : (
              <div className="text-3xl font-mono font-bold text-blue-400">
                {plcData.presion.toFixed(2)}
              </div>
            )}
          </div>
          <span className="text-xs text-gray-500">Bar</span>
          
          {/* Pequeño icono de lápiz que aparece al pasar el ratón (indicador visual de que es editable) */}
          {!isEditing && (
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4 text-blue-400">
                <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L6.832 19.82a4.5 4.5 0 0 1-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 0 1 1.13-1.897L16.863 4.487Zm0 0L19.5 7.125" />
              </svg>
            </div>
          )}
        </div>

        {/* Tarjeta Variable 2: TEMPERATURA (Solo lectura) */}
        <div className="text-center p-4 bg-gray-900 rounded border border-orange-500 opacity-90">
          <p className="text-gray-400 text-sm mb-1">Temp</p>
          <div className="h-10 flex items-center justify-center">
             <div className="text-3xl font-mono font-bold text-orange-400">
               {plcData.temperatura.toFixed(1)}
             </div>
          </div>
          <span className="text-xs text-gray-500">°C</span>
        </div>
      </div>
      
      {/* Texto de ayuda inferior */}
      <p className="text-xs text-gray-500 text-center mt-4">
        Haz clic sobre la presión, ingresa el nuevo valor y presiona <b>Enter</b> para enviar al PLC.
      </p>
    </div>
  );
}