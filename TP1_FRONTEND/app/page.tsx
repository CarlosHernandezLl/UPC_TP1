"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

type SystemStatus = "En Línea" | "PLC Desconectado" | "Node-RED Caído" | "Backend Caído" | "Verificando...";

export default function HomePage() {
  const [status, setStatus] = useState<SystemStatus>("Verificando...");

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/plc/status`);
        
        // Si el fetch falla (ej. error 500), saltará al catch
        if (!res.ok) throw new Error("Error HTTP");

        const data = await res.json();

        // Evaluamos en orden de gravedad
        if (!data.node_red_connected) {
          setStatus("Node-RED Caído");
        } else if (!data.plc_connected) {
          setStatus("PLC Desconectado");
        } else {
          setStatus("En Línea");
        }
      } catch (error) {
        // Si el servidor FastAPI está apagado, el fetch lanza un error de red
        setStatus("Backend Caído");
      }
    };

    // Consultamos inmediatamente y luego cada 5 segundos
    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const statusStyles: Record<SystemStatus, string> = {
    "En Línea":           "text-green-500",
    "PLC Desconectado":   "text-yellow-400",
    "Node-RED Caído":     "text-orange-500",
    "Backend Caído":      "text-red-600",
    "Verificando...":     "text-gray-400",
  };

  const statusDot: Record<SystemStatus, string> = {
    "En Línea":           "●",
    "PLC Desconectado":   "◐",
    "Node-RED Caído":     "○",
    "Backend Caído":      "❌",
    "Verificando...":     "○",
  };

  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <h1 className="text-5xl font-bold text-white mb-4">Bienvenido</h1>
      <p className="text-xl text-gray-400 max-w-2xl">
        Selecciona una opción en el menú lateral para comenzar.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-12">
        <div className="p-6 bg-gray-900 rounded-lg border border-gray-800">
          <h3 className="text-blue-400 font-bold text-xl">Estado del Sistema</h3>
          <p className={`mt-2 text-lg font-semibold ${statusStyles[status]}`}>
            {statusDot[status]} {status}
          </p>
        </div>
      </div>
    </div>
  );
}