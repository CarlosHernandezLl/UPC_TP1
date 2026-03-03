"use client";

import { useState, useEffect } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export default function PLCTrend() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  // Por defecto, mostramos las últimas 2 horas
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setHours(d.getHours() - 2);
    // Formato requerido por <input type="datetime-local"> (YYYY-MM-DDThh:mm)
    return d.toISOString().slice(0, 16); 
  });
  
  const [endDate, setEndDate] = useState(() => {
    return new Date().toISOString().slice(0, 16);
  });

  const fetchHistory = async () => {
    setLoading(true);
    try {
      // Obtenemos el token para la autorización (asumiendo que tu ruta lo requiera)
      const token = document.cookie
        .split("; ")
        .find((row) => row.startsWith("scada_token="))
        ?.split("=")[1];

      // Construimos la URL con los parámetros de fecha
      const url = new URL(`${API_URL}/plc/history`);
      if (startDate) url.searchParams.append("start", new Date(startDate).toISOString());
      if (endDate) url.searchParams.append("end", new Date(endDate).toISOString());

      const res = await fetch(url.toString(), {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        const result = await res.json();
        // Formatear la fecha para que se vea bonita en el eje X (ej. "14:30:00")
        const formattedData = result.map((item: any) => {
            const dateObj = new Date(item.fecha);
            return {
                ...item,
                hora: dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            }
        });
        setData(formattedData);
      } else {
        console.error("Error al obtener histórico");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Cargar datos al montar el componente
  useEffect(() => {
    fetchHistory();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="p-6 bg-gray-800 rounded-lg border border-gray-700 text-white w-full mt-8">
      <h2 className="text-2xl font-bold mb-6 text-blue-400">Tendencia de Presión Histórica</h2>

      {/* Controles de Filtro */}
      <div className="flex flex-wrap gap-4 items-end mb-6 bg-gray-900 p-4 rounded border border-gray-700">
        <div className="flex flex-col">
          <label className="text-xs text-gray-400 mb-1">Desde</label>
          <input
            type="datetime-local"
            className="p-2 rounded bg-gray-800 text-white border border-gray-600 focus:border-blue-500 outline-none"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>
        <div className="flex flex-col">
          <label className="text-xs text-gray-400 mb-1">Hasta</label>
          <input
            type="datetime-local"
            className="p-2 rounded bg-gray-800 text-white border border-gray-600 focus:border-blue-500 outline-none"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>
        <button
          onClick={fetchHistory}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded font-semibold transition-colors disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Cargando..." : "Filtrar"}
        </button>
      </div>

      {/* Gráfica Recharts */}
      <div className="h-96 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="hora" stroke="#9CA3AF" tick={{ fontSize: 12 }} />
            <YAxis stroke="#9CA3AF" tick={{ fontSize: 12 }} unit=" Bar" />
            
            {/* Tooltip personalizado al pasar el ratón */}
            <Tooltip 
              contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
              itemStyle={{ color: '#60A5FA' }}
            />
            
            {/* La línea de la gráfica */}
            <Line 
              type="monotone" 
              dataKey="presion" 
              name="Presión" 
              stroke="#3B82F6" 
              strokeWidth={3} 
              dot={false} 
              activeDot={{ r: 8 }} 
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}