"use client";

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ScatterChart, Scatter
} from 'recharts';
import {
  ArrowTrendingUpIcon,
  BoltIcon,
  CurrencyDollarIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ArrowPathRoundedSquareIcon
} from '@heroicons/react/24/outline';

// 1. Importamos el servicio que conecta con tu FastAPI
import { aiService, DashboardMetrics } from '@/services/aiService';

export default function Dashboard() {
  const [kwhCost, setKwhCost] = useState(0.15);
  const [isClient, setIsClient] = useState(false);

  // 2. Nuevos estados para manejar la data real del Backend
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 3. Efecto para cargar los datos al montar el componente
  useEffect(() => {
    setIsClient(true);
    cargarMetricas();
  }, []);

  const cargarMetricas = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Llamada real al endpoint GET /ai/dashboard-metrics
      const data = await aiService.getDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
      setError("No se pudieron cargar los datos históricos del servidor.");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isClient) return null;

  // Pantalla de Carga (Mientras el backend procesa o consulta Supabase)
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-slate-500 bg-gray-50">
        <ArrowPathRoundedSquareIcon className="w-12 h-12 animate-spin mb-4 text-blue-500" />
        <p className="font-bold">Consultando Data de Oro en Supabase...</p>
      </div>
    );
  }

  // Pantalla de Error
  if (error || !metrics) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
        <div className="bg-rose-50 border border-rose-200 p-6 rounded-xl text-center max-w-md">
          <ExclamationTriangleIcon className="w-12 h-12 text-rose-500 mx-auto mb-4" />
          <h3 className="text-rose-800 font-bold mb-2">Error de Conexión</h3>
          <p className="text-rose-600 text-sm">{error}</p>
          <button onClick={cargarMetricas} className="mt-4 px-4 py-2 bg-rose-500 text-white rounded-lg font-bold hover:bg-rose-600">Reintentar</button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">

        {/* Header con Enfoque de Auditoría */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Análisis de Optimización Energética</h1>
            <p className="text-sm text-slate-500">Evaluación de Desempeño mediante Modelo Estacionario XGBoost</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="text-[10px] font-black text-blue-700 bg-blue-50 border border-blue-100 px-3 py-1 rounded-md uppercase">
              Modelo Activo
            </span>
            <span className="text-[10px] font-medium text-slate-400">Datos en Tiempo Real de BD</span>
          </div>
        </div>

        {/* KPIs de Impacto Económico Dinámicos */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MetricCard
            title="Ahorro Potencial (Periodo)"
            // Multiplicamos el diferencial dinámico devuelto por la BD por el costo ingresado por el usuario
            value={`$${(metrics.kpi_diferencial * kwhCost).toFixed(2)}`}
            trend="Activo"
            icon={CurrencyDollarIcon}
            color="bg-green-500"
          />
          <MetricCard
            title="Diferencial Energético"
            value={`${metrics.kpi_diferencial.toFixed(1)} kWh`}
            subtitle="Brecha entre Real e Ideal"
            icon={BoltIcon}
            color="bg-blue-500"
          />
          <MetricCard
            title="Métrica de Ajuste (R²)"
            value={`${metrics.r2_score}%`}
            subtitle="Precisión en Estado Estacionario"
            icon={ShieldCheckIcon}
            color="bg-cyan-500"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Gráfico de Auditoría Histórica Ajustado para SSD */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-800">Auditoría Estacionaria: Consumo Real vs. Recomendación IA</h2>
                <p className="text-xs text-slate-400 font-medium">
                  Evaluación sobre las últimas 24 ventanas en estado estable (Filtro SSD - Data de Oro)
                </p>
              </div>
              <div className="flex gap-4">
                <LegendItem color="bg-rose-400" label="Real (PLC)" />
                <LegendItem color="bg-blue-500" label="Ideal (ML)" />
              </div>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={metrics.auditData}>
                  <defs>
                    <linearGradient id="colorIdeal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />

                  {/* ⬅️ CAMBIO CRÍTICO: Usamos sample_id como el identificador discreto del eje X */}
                  <XAxis dataKey="sample_id" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 9 }} angle={-15} textAnchor="end" height={50} />

                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} unit="%" />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 16px rgba(0,0,0,0.05)' }} />
                  <Area type="monotone" dataKey="ideal" name="Potencia Ideal (%)" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorIdeal)" />
                  {/* Usamos type="linear" o dot={true} si prefieres remarcar que son puntos discretos de auditoría */}
                  <Line type="linear" dataKey="real" name="Potencia Real (%)" stroke="#fb7185" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Ajuste de Parámetros de Simulación */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Configuración de Costos</h2>
            <div className="space-y-6 grow">
              <div>
                <label className="block text-[10px] font-black text-slate-400 uppercase mb-2">Costo kWh (USD)</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-3 flex items-center text-slate-400 font-bold">$</span>
                  <input
                    type="number" step="0.01" min="0"
                    value={kwhCost}
                    onChange={(e) => setKwhCost(parseFloat(e.target.value) || 0)}
                    className="w-full pl-8 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none font-bold text-slate-700 transition-all"
                  />
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-xl border border-blue-100">
                <div className="flex gap-3">
                  <ExclamationTriangleIcon className="text-blue-500 w-5 h-5 shrink-0" />
                  <p className="text-[10px] text-slate-600 font-medium leading-relaxed">
                    Al modificar la tarifa eléctrica, el panel recalcula automáticamente el ahorro del periodo basado en los <span className="font-bold text-blue-700">{metrics.kpi_diferencial.toFixed(1)} kWh</span> detectados como sobreconsumo por el Gemelo Digital.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Firma Térmica del Modelo */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 mb-6">Firma Térmica: Relación Histórica Humedad vs Potencia</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              {/* Inyectamos la data dinámica metrics.modelCorrelation */}
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" dataKey="hum" name="Humedad Sala" unit="%" axisLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} domain={['auto', 'auto']} />
                <YAxis type="number" dataKey="pwr" name="Potencia Secador" unit="%" axisLine={false} tick={{ fill: '#94a3b8', fontSize: 11 }} domain={['auto', 'auto']} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Registros Estacionarios" data={metrics.modelCorrelation} fill="#06b6d4" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

// ... (MetricCard y LegendItem se mantienen exactamente igual que en tu código)
function MetricCard({ title, value, trend, subtitle, icon: Icon, color }: any) {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
      <div className={`absolute top-0 left-0 w-1.5 h-full ${color}`}></div>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</span>
        <Icon className={`w-6 h-6 opacity-20 group-hover:opacity-100 transition-opacity ${color.replace('bg-', 'text-')}`} />
      </div>
      <div className="text-3xl font-bold text-slate-800 tracking-tight">{value}</div>
      {trend && <div className="text-[10px] text-green-600 mt-2 font-black uppercase tracking-tighter">↑ {trend}</div>}
      {subtitle && <div className="text-[10px] text-slate-400 mt-2 font-medium italic">{subtitle}</div>}
    </div>
  );
}

function LegendItem({ color, label }: { color: string, label: string }) {
  return (
    <span className="flex items-center text-[10px] font-black text-slate-400 uppercase tracking-tighter">
      <span className={`w-2 h-2 ${color} rounded-full mr-2`}></span> {label}
    </span>
  );
}