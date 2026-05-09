'use client';

import React, { useState } from 'react';
import { 
  AdjustmentsHorizontalIcon, 
  CloudIcon, 
  BoltIcon, 
  BeakerIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  VariableIcon,
  HandThumbUpIcon,
  HandThumbDownIcon
} from '@heroicons/react/24/outline';

export default function Simulator() {
  const [isCalculating, setIsCalculating] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [prediction, setPrediction] = useState(24.5); // Simulación de resultado IA

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Simulador de Optimización Energética</h1>
          <p className="text-slate-500 text-sm">Ingrese las condiciones actuales para obtener la recomendación de potencia del XGBoost.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Columna Izquierda: Entradas Manuales (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2 border-b pb-4">
                <AdjustmentsHorizontalIcon className="w-5 h-5 text-blue-600" />
                Variables de Operación
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
                {/* Grupo: Clima Exterior */}
                <div className="space-y-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <CloudIcon className="w-4 h-4" /> Entorno Exterior
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Temp. Exterior (°C)</label>
                      <input type="number" placeholder="21.5" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Ext. (%)</label>
                      <input type="number" placeholder="78" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  </div>
                </div>

                {/* Grupo: Condiciones UMA */}
                <div className="space-y-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <VariableIcon className="w-4 h-4" /> Entrada Aire (UMA)
                  </h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Temp. UMA (°C)</label>
                      <input type="number" placeholder="23.2" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Hum. UMA (%)</label>
                      <input type="number" placeholder="42" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                  </div>
                </div>

                {/* Grupo: Datos de Sala y Secador */}
                <div className="space-y-4 md:col-span-2 pt-4 border-t border-slate-50">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <BeakerIcon className="w-4 h-4" /> Estado de la Sala
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Potencia Actual (%)</label>
                      <input type="number" placeholder="80" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Sala Actual (%)</label>
                      <input type="number" placeholder="52.4" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500" />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Setpoint Objetivo (%)</label>
                      <input type="number" placeholder="50" className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 border-blue-200 bg-blue-50" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button 
                  onClick={() => { setIsCalculating(true); setTimeout(() => { setIsCalculating(false); setShowResult(true); }, 1500); }}
                  className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-800 transition-all shadow-lg shadow-slate-200"
                >
                  {isCalculating ? <ArrowPathIcon className="w-5 h-5 animate-spin" /> : <BoltIcon className="w-5 h-5" />}
                  {isCalculating ? 'Consultando IA...' : 'Generar Recomendación'}
                </button>
              </div>
            </div>

            {/* Alerta de Riesgo (Dinámica) */}
            {showResult && (
              <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex gap-4 animate-pulse">
                <ExclamationTriangleIcon className="w-8 h-8 text-rose-500 flex-shrink-0" />
                <div>
                  <h4 className="text-rose-800 font-bold text-sm uppercase">Riesgo de Incumplimiento GMP</h4>
                  <p className="text-rose-700 text-xs">La predicción indica que con la potencia actual, la humedad podría exceder el límite del 55% en los próximos 15 minutos.</p>
                </div>
              </div>
            )}
          </div>

          {/* Columna Derecha: Resultado de Recomendación (1/3) */}
          <div className="space-y-6">
            <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-2 bg-blue-600"></div>
              <h2 className="text-slate-400 font-bold text-xs uppercase tracking-widest mb-4">Potencia Recomendada</h2>
              
              {showResult ? (
                <div className="space-y-4">
                  <div className="text-6xl font-black text-slate-900">{prediction}%</div>
                  <div className="text-sm font-bold text-blue-600 bg-blue-50 py-2 rounded-lg">Ahorro Estimado: 14.2%</div>
                  
                  <div className="pt-6 border-t border-slate-100">
                    <p className="text-xs text-slate-500 mb-4 font-medium">¿Aplicará esta recomendación en el tablero físico?</p>
                    <div className="flex gap-2">
                      <button className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                        <HandThumbUpIcon className="w-4 h-4" /> SÍ, APLICADA
                      </button>
                      <button className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-600 py-2 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors">
                        <HandThumbDownIcon className="w-4 h-4" /> IGNORAR
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-12 space-y-3">
                  <BoltIcon className="w-12 h-12 text-slate-200 mx-auto" />
                  <p className="text-slate-400 text-xs italic font-medium px-4">Esperando entrada de datos para procesar con XGBoost...</p>
                </div>
              )}
            </div>

            {/* Audit Log Rápido */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h3 className="text-xs font-bold text-slate-700 uppercase mb-4 flex items-center gap-2">
                <CheckCircleIcon className="w-4 h-4 text-emerald-500" />
                Últimas Acciones
              </h3>
              <div className="space-y-4">
                <div className="text-[10px] border-l-2 border-emerald-500 pl-3">
                  <p className="font-bold text-slate-800">Recomendación Aplicada (22.0%)</p>
                  <p className="text-slate-400">Usuario: Supervisor_01 • Hace 10 min</p>
                </div>
                <div className="text-[10px] border-l-2 border-slate-300 pl-3">
                  <p className="font-bold text-slate-500">Simulación generada</p>
                  <p className="text-slate-400">Usuario: Supervisor_01 • Hace 45 min</p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}