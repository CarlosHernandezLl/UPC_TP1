'use client';

import React, { useState } from 'react';
import { 
  CpuChipIcon, 
  ArrowPathIcon, 
  AdjustmentsVerticalIcon, 
  BeakerIcon,
  ShieldCheckIcon,
  ServerIcon,
  CheckBadgeIcon,
  InformationCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

export default function IAControl() {
  const [isTraining, setIsTraining] = useState(false);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Centro de Control de IA</h1>
            <p className="text-slate-500 text-sm">Gestión del microservicio de Machine Learning y parámetros de cumplimiento GMP.</p>
          </div>
          {/* Status del Microservicio (Puerto 8001) */}
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
            <ServerIcon className="w-5 h-5 text-slate-400" />
            <span className="text-xs font-bold text-slate-500 uppercase">ML Service:</span>
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
              <span className="text-xs font-bold text-green-600">ONLINE (8001)</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Columna Izquierda: Entrenamiento y Salud del Modelo (2/3) */}
          <div className="lg:col-span-2 space-y-6">
            
            {/* Card: Ejecución de Entrenamiento */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                  <CpuChipIcon className="w-5 h-5 text-indigo-500" />
                  Entrenamiento del Modelo
                </h2>
                <span className="text-[10px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded uppercase">XGBoost Regressor</span>
              </div>
              
              <div className="bg-slate-50 p-6 rounded-xl border border-slate-100 mb-6">
                <div className="flex flex-col items-center text-center">
                  <div className={`p-4 rounded-full mb-4 ${isTraining ? 'bg-indigo-100' : 'bg-slate-200'}`}>
                    <ArrowPathIcon className={`w-10 h-10 ${isTraining ? 'text-indigo-600 animate-spin' : 'text-slate-400'}`} />
                  </div>
                  <h3 className="text-slate-800 font-bold mb-1">
                    {isTraining ? 'Entrenando Cerebro Digital...' : 'Modelo Listo para Re-entrenamiento'}
                  </h3>
                  <p className="text-slate-500 text-xs mb-6 max-w-sm">
                    Al iniciar, el sistema extraerá los datos sincronizados de la BD y ajustará los hiperparámetros del modelo de predicción energética.
                  </p>
                  <button 
                    onClick={() => setIsTraining(true)}
                    disabled={isTraining}
                    className={`px-8 py-3 rounded-lg font-bold text-white transition-all shadow-lg ${isTraining ? 'bg-slate-400' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-100'}`}
                  >
                    {isTraining ? 'Procesando Red Neuronal...' : 'Disparar Entrenamiento'}
                  </button>
                </div>
              </div>

              {/* Métricas de Calidad */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border border-slate-100 rounded-lg bg-white">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Precisión (R²)</span>
                  <div className="text-2xl font-bold text-slate-800">0.9824</div>
                </div>
                <div className="p-4 border border-slate-100 rounded-lg bg-white">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Error Medio (MSE)</span>
                  <div className="text-2xl font-bold text-slate-800">0.0014</div>
                </div>
                <div className="p-4 border border-slate-100 rounded-lg bg-white">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Última Versión</span>
                  <div className="text-sm font-bold text-indigo-600 mt-1">v2.4.0-stable</div>
                </div>
              </div>
            </div>

            {/* Logs de IA */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Log de Eventos de IA</h3>
                <span className="text-[10px] text-slate-400">Mostrando últimos 3 eventos</span>
              </div>
              <div className="divide-y divide-slate-100">
                <div className="p-4 flex gap-3">
                  <CheckBadgeIcon className="w-5 h-5 text-green-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-slate-700">Entrenamiento Exitoso</p>
                    <p className="text-[11px] text-slate-500">Modelo guardado como hvac_model_v1.joblib (2,880 filas usadas).</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">Hace 45 minutos</span>
                  </div>
                </div>
                <div className="p-4 flex gap-3">
                  <InformationCircleIcon className="w-5 h-5 text-blue-500 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-bold text-slate-700">Cambio de Hiperparámetros</p>
                    <p className="text-[11px] text-slate-500">Ajuste de learning_rate a 0.05 para reducir sobreajuste.</p>
                    <span className="text-[10px] text-slate-400 mt-1 block">Ayer, 18:20</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Columna Derecha: Parámetros de Seguridad GMP (1/3) */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <ShieldCheckIcon className="w-5 h-5 text-emerald-500" />
                Límites de Seguridad (GMP)
              </h2>

              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Humedad Relativa Mínima (%)</label>
                  <input type="number" defaultValue="45" className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none font-bold" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Humedad Relativa Máxima (%)</label>
                  <input type="number" defaultValue="55" className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-emerald-500 outline-none font-bold" />
                </div>
                
                <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                  <div className="flex gap-2">
                    <ExclamationCircleIcon className="w-5 h-5 text-emerald-600 flex-shrink-0" />
                    <p className="text-[11px] text-emerald-800 leading-relaxed font-medium">
                      <span className="font-bold">Protocolo Farmacéutico:</span> Estos límites dispararán una alerta visual de "Riesgo de Incumplimiento" en el panel del Supervisor si la predicción de la IA sale de rango.
                    </p>
                  </div>
                </div>

                <button className="w-full bg-slate-900 text-white font-bold py-3 rounded-lg hover:bg-slate-800 transition-colors flex items-center justify-center gap-2">
                  <AdjustmentsVerticalIcon className="w-5 h-5" />
                  Guardar Configuración
                </button>
              </div>
            </div>

            {/* Estado de Salud del Modelo */}
            <div className="bg-indigo-600 p-6 rounded-xl shadow-lg shadow-indigo-100 text-white">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-sm uppercase tracking-wider">
                <BeakerIcon className="w-5 h-5 text-indigo-200" />
                Validación de Sesgo
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between text-xs">
                  <span className="text-indigo-100">Integridad de Datos</span>
                  <span className="font-bold">100%</span>
                </div>
                <div className="w-full bg-indigo-500 rounded-full h-1.5">
                  <div className="bg-white h-1.5 rounded-full w-[100%]"></div>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-indigo-100">Estabilidad Térmica</span>
                  <span className="font-bold">94%</span>
                </div>
                <div className="w-full bg-indigo-500 rounded-full h-1.5">
                  <div className="bg-white h-1.5 rounded-full w-[94%]"></div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}