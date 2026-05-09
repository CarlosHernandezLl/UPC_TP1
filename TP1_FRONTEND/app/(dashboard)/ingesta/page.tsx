'use client';

import React, { useState } from 'react';
import { 
  CloudArrowUpIcon, 
  CalendarIcon, 
  CheckCircleIcon, 
  DocumentTextIcon,
  ArrowPathIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

export default function DataIngestion() {
  const [isProcessing, setIsProcessing] = useState(false);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Ingesta de Datos Históricos</h1>
          <p className="text-slate-500 text-sm">Carga y sincronización de datasets para entrenamiento del modelo XGBoost.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Columna Izquierda: Carga de Archivos (2/3 de ancho) */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <DocumentTextIcon className="w-5 h-5 text-blue-500" />
                Selección de Archivos (CSV)
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* File Input: PLC */}
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 hover:border-blue-400 transition-colors text-center">
                  <CloudArrowUpIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Datos PLC</span>
                  <input type="file" className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                </div>

                {/* File Input: Datalogger */}
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 hover:border-blue-400 transition-colors text-center">
                  <CloudArrowUpIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Datalogger Sala</span>
                  <input type="file" className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                </div>

                {/* File Input: Exterior */}
                <div className="border-2 border-dashed border-slate-200 rounded-lg p-4 hover:border-blue-400 transition-colors text-center">
                  <CloudArrowUpIcon className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                  <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Clima Exterior</span>
                  <input type="file" className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
                </div>
              </div>
            </div>

            {/* Tabla de logs de procesamiento */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 bg-slate-50">
                <h3 className="text-sm font-bold text-slate-700 uppercase tracking-wider">Historial de Procesamiento</h3>
              </div>
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-100">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-[11px] uppercase">Fecha Carga</th>
                    <th className="px-4 py-3 font-semibold text-[11px] uppercase">Rango de Datos</th>
                    <th className="px-4 py-3 font-semibold text-[11px] uppercase">Registros</th>
                    <th className="px-4 py-3 font-semibold text-[11px] uppercase">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  <tr>
                    <td className="px-4 py-3 font-medium text-slate-700">26/04/2026 14:20</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">23/04 - 25/04</td>
                    <td className="px-4 py-3 text-slate-600">2,880</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 text-green-600 bg-green-50 px-2 py-1 rounded text-[10px] font-bold uppercase">
                        <CheckCircleIcon className="w-3 h-3" /> Sincronizado
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 font-medium text-slate-700">25/04/2026 09:15</td>
                    <td className="px-4 py-3 text-slate-500 text-xs">20/04 - 22/04</td>
                    <td className="px-4 py-3 text-slate-600">0</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-1 text-rose-600 bg-rose-50 px-2 py-1 rounded text-[10px] font-bold uppercase">
                        <ExclamationCircleIcon className="w-3 h-3" /> Error Columnas
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Columna Derecha: Configuración de Corte (1/3 de ancho) */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <CalendarIcon className="w-5 h-5 text-blue-500" />
                Punto de Corte
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Fecha/Hora Inicio</label>
                  <input type="datetime-local" className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Fecha/Hora Fin</label>
                  <input type="datetime-local" className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-blue-500 outline-none" />
                </div>

                <div className="pt-4">
                  <button 
                    onClick={() => setIsProcessing(true)}
                    disabled={isProcessing}
                    className={`w-full flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-bold text-white transition-all shadow-lg shadow-blue-100 ${isProcessing ? 'bg-slate-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
                  >
                    {isProcessing ? (
                      <ArrowPathIcon className="w-5 h-5 animate-spin" />
                    ) : (
                      <CloudArrowUpIcon className="w-5 h-5" />
                    )}
                    {isProcessing ? 'Procesando Dataset...' : 'Procesar e Inyectar'}
                  </button>
                </div>

                <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                  <p className="text-[11px] text-blue-700 leading-relaxed">
                    <span className="font-bold">Aviso:</span> Al procesar, el sistema realizará un <span className="italic">merge_asof</span> para sincronizar los archivos y aplicará una interpolación lineal para normalizar la data a intervalos de 1 minuto.
                  </p>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}