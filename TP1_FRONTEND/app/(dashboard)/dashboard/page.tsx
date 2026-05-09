"use client";

import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ScatterChart, Scatter 
} from 'recharts';
import { 
  ArrowTrendingUpIcon, 
  BoltIcon, 
  ChartBarIcon, 
  CurrencyDollarIcon, 
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

// Datos de Auditoría: Comparativa de un lote de producción previo
const auditData = [
  { time: '00:00', real: 45, ideal: 40 },
  { time: '04:00', real: 52, ideal: 42 },
  { time: '08:00', real: 78, ideal: 55 },
  { time: '12:00', real: 95, ideal: 65 },
  { time: '16:00', real: 88, ideal: 60 },
  { time: '20:00', real: 65, ideal: 48 },
  { time: '23:59', real: 48, ideal: 38 },
];

// Correlación Estacionaria: Humedad vs Potencia Recomendada por XGBoost
const modelCorrelation = [
  { hum: 40, pwr: 30 }, { hum: 55, pwr: 45 }, { hum: 60, pwr: 55 },
  { hum: 75, pwr: 70 }, { hum: 85, pwr: 88 }, { hum: 90, pwr: 95 },
];

export default function Dashboard() {
  const [kwhCost, setKwhCost] = useState(0.15);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  if (!isClient) return null;

  return (
    <div className="p-6 min-h-screen">
      <div className="max-w-7xl mx-auto">
        
        {/* Header con Enfoque de Auditoría */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Análisis de Optimización Energética</h1>
            <p className="text-sm text-slate-500">Evaluación de Desempeño mediante Modelo Estacionario XGBoost</p>
          </div>
          <div className="flex flex-col items-end gap-2">
            <span className="text-[10px] font-black text-primary bg-blue-50 border border-blue-100 px-3 py-1 rounded-md uppercase">
              Modelo: XGBoost_HVAC_v1.2
            </span>
            <span className="text-[10px] font-medium text-slate-400">Último Reporte: 29/04/2026</span>
          </div>
        </div>

        {/* KPIs de Impacto Económico */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <MetricCard 
            title="Ahorro Potencial (Periodo)" 
            value={`$${(450.2 * kwhCost).toFixed(2)}`} 
            trend="+12.5%" 
            icon={CurrencyDollarIcon} 
            color="bg-green-500" 
          />
          <MetricCard 
            title="Diferencial Energético" 
            value="450.2 kWh" 
            subtitle="Brecha entre Real e Ideal" 
            icon={BoltIcon} 
            color="bg-primary" 
          />
          <MetricCard 
            title="Métrica de Ajuste (R²)" 
            value="98.2%" 
            subtitle="Precisión en Estado Estacionario" 
            icon={ShieldCheckIcon} 
            color="bg-cyan-500" 
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Gráfico de Auditoría Histórica */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-border shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-800">Desempeño: Consumo Real vs. Recomendación IA</h2>
                <p className="text-xs text-slate-400 font-medium">Análisis basado en datos históricos del proceso HVAC</p>
              </div>
              <div className="flex gap-4">
                <LegendItem color="bg-rose-400" label="Real (PLC)" />
                <LegendItem color="bg-primary" label="Ideal (ML)" />
              </div>
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={auditData}>
                  <defs>
                    <linearGradient id="colorIdeal" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0284c7" stopOpacity={0.1}/>
                      <stop offset="95%" stopColor="#0284c7" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 11}} />
                  <YAxis axisLine={false} tickLine={false} tick={{fill: '#94a3b8', fontSize: 11}} />
                  <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 16px rgba(0,0,0,0.05)' }} />
                  <Area type="monotone" dataKey="ideal" stroke="#0284c7" strokeWidth={3} fillOpacity={1} fill="url(#colorIdeal)" />
                  <Line type="monotone" dataKey="real" stroke="#fb7185" strokeWidth={2} strokeDasharray="5 5" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Ajuste de Parámetros de Simulación */}
          <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
            <h2 className="text-lg font-bold text-slate-800 mb-4">Configuración de Costos</h2>
            <div className="space-y-6">
              <div>
                <label className="block text-[10px] font-black text-slate-400 uppercase mb-2">Costo kWh (USD)</label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-3 flex items-center text-slate-400 font-bold">$</span>
                  <input 
                    type="number" step="0.01" min="0"
                    value={kwhCost}
                    onChange={(e) => setKwhCost(parseFloat(e.target.value) || 0)}
                    className="w-full pl-8 pr-4 py-3 bg-slate-50 border border-border rounded-lg focus:ring-2 focus:ring-primary outline-none font-bold text-slate-700 transition-all"
                  />
                </div>
              </div>
              <button className="w-full bg-slate-900 hover:bg-primary text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 group shadow-md shadow-slate-200">
                <ArrowPathIcon className="w-5 h-5 group-hover:rotate-180 transition-transform duration-700" />
                Recalcular Ahorro
              </button>
              
              <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-100/50">
                <div className="flex gap-3">
                  <ExclamationTriangleIcon className="text-primary w-5 h-5 flex-shrink-0" />
                  <p className="text-[10px] text-slate-600 font-medium leading-relaxed">
                    Este valor se utiliza para proyectar el ROI y el ahorro económico acumulado en los informes GxP.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Firma Térmica del Modelo */}
        <div className="bg-white p-6 rounded-xl border border-border shadow-sm">
          <h2 className="text-lg font-bold text-slate-800 mb-6">Firma Térmica: Sensibilidad a la Humedad Exterior</h2>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" dataKey="hum" name="Humedad" unit="%" axisLine={false} tick={{fill: '#94a3b8', fontSize: 11}} />
                <YAxis type="number" dataKey="pwr" name="Potencia" unit="kW" axisLine={false} tick={{fill: '#94a3b8', fontSize: 11}} />
                <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Puntos de Entrenamiento" data={modelCorrelation} fill="#06b6d4" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}

function MetricCard({ title, value, trend, subtitle, icon: Icon, color }: any) {
  return (
    <div className="bg-white p-6 rounded-xl border border-border shadow-sm relative overflow-hidden group hover:shadow-md transition-all">
      <div className={`absolute top-0 left-0 w-1.5 h-full ${color}`}></div>
      <div className="flex items-center justify-between mb-3">
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{title}</span>
        <Icon className={`w-6 h-6 opacity-20 group-hover:opacity-100 transition-opacity ${color.replace('bg-', 'text-')}`} />
      </div>
      <div className="text-3xl font-bold text-slate-800 tracking-tight">{value}</div>
      {trend && <div className="text-[10px] text-green-600 mt-2 font-black uppercase tracking-tighter">↑ {trend} <span className="text-slate-400 font-normal lowercase ml-1">vs histórico</span></div>}
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