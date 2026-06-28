'use client';

import React, { useEffect, useState } from 'react';
import {
  CloudArrowUpIcon,
  CalendarIcon,
  CheckCircleIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

import { dataService, IngestionLog } from '@/services/dataService'; // Importas tu servicio
import { useToast } from '@/components/ui/toast';

export default function DataIngestion() {
  const { showToast } = useToast();
  const acceptedFileTypes = ".csv,.txt,.xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  const [isProcessing, setIsProcessing] = useState(false);
  const [history, setHistory] = useState<IngestionLog[]>([]);

  const [filePlc, setFilePlc] = useState<File | null>(null);
  const [fileLog, setFileLog] = useState<File | null>(null);
  const [fileExt, setFileExt] = useState<File | null>(null);

  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  const fetchHistory = async () => {
    try {
      const data = await dataService.getIngestionHistory();
      setHistory(data);
    } catch (error) {
      console.error("Error al obtener el historial:", error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleProcessAndInject = async () => {
    if (!filePlc || !fileLog || !fileExt) {
      // alert("Por favor, selecciona los 3 archivos requeridos (PLC, Datalogger y Clima) antes de continuar.");
      showToast('error', 'Por favor, selecciona los 3 archivos requeridos (PLC, Datalogger y Clima) antes de continuar.')
      return;
    }

    setIsProcessing(true);

    try {
      const result = await dataService.uploadHvacData(
        filePlc,
        fileLog,
        fileExt,
        startDate || undefined,
        endDate || undefined
      );

      showToast('success', '¡Dataset procesado y sincronizado con éxito!')

      // alert(result.message || "¡Dataset procesado y sincronizado con éxito!");

      setFilePlc(null);
      setFileLog(null);
      setFileExt(null);

      await fetchHistory();
    } catch (error) {
      console.error("Error inyectando el dataset:", error);
      alert("Ocurrió un error crítico al procesar el pipeline termodinámico. Revisa los logs del servidor.");
    } finally {
      setIsProcessing(false);
    }
  };

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
                <div className={`border-2 border-dashed rounded-lg p-4 transition-colors text-center flex flex-col items-center justify-center ${filePlc ? 'border-green-400 bg-green-50/30' : 'border-slate-200 hover:border-blue-400'}`}>
                  <CloudArrowUpIcon className={`w-8 h-8 mx-auto mb-2 ${filePlc ? 'text-green-500' : 'text-slate-400'}`} />
                  <div>
                    <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Datos PLC</span>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFilePlc(e.target.files?.[0] || null)}
                      className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {filePlc && <p className="text-[10px] text-green-600 mt-1 font-medium truncate max-w-35">{filePlc.name}</p>}
                  </div>
                </div>

                {/* File Input: Datalogger */}
                <div className={`border-2 border-dashed rounded-lg p-4 transition-colors text-center flex flex-col items-center justify-center ${fileLog ? 'border-green-400 bg-green-50/30' : 'border-slate-200 hover:border-blue-400'}`}>
                  <CloudArrowUpIcon className={`w-8 h-8 mx-auto mb-2 ${fileLog ? 'text-green-500' : 'text-slate-400'}`} />
                  <div>
                    <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Datalogger Sala</span>
                    <input
                      type="file"
                      accept={acceptedFileTypes}
                      onChange={(e) => setFileLog(e.target.files?.[0] || null)}
                      className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {fileLog && <p className="text-[10px] text-green-600 mt-1 font-medium truncate max-w-35">{fileLog.name}</p>}
                  </div>
                </div>

                {/* File Input: Clima Exterior */}
                <div className={`border-2 border-dashed rounded-lg p-4 transition-colors text-center flex flex-col items-center justify-center ${fileExt ? 'border-green-400 bg-green-50/30' : 'border-slate-200 hover:border-blue-400'}`}>
                  <CloudArrowUpIcon className={`w-8 h-8 mx-auto mb-2 ${fileExt ? 'text-green-500' : 'text-slate-400'}`} />
                  <div>
                    <span className="block text-xs font-bold text-slate-500 uppercase mb-2">Clima Exterior</span>
                    <input
                      type="file"
                      accept=".csv"
                      onChange={(e) => setFileExt(e.target.files?.[0] || null)}
                      className="text-[10px] text-slate-500 file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {fileExt && <p className="text-[10px] text-green-600 mt-1 font-medium truncate max-w-35">{fileExt.name}</p>}
                  </div>
                </div>
              </div>
            </div>

            {/* Renderizado Dinámico de la Tabla del Historial */}
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
                  {history.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="text-center py-6 text-slate-400 text-xs">
                        No se han encontrado registros en el historial de logs de ingesta.
                      </td>
                    </tr>
                  ) : (
                    history.map((log) => (
                      <tr key={log.id}>
                        <td className="px-4 py-3 font-medium text-slate-700">
                          {new Date(log.fecha_carga).toLocaleString('es-PE')}
                        </td>
                        <td className="px-4 py-3 text-slate-500 text-xs">{log.rango_datos}</td>
                        <td className="px-4 py-3 text-slate-600">{log.registros.toLocaleString()}</td>
                        <td className="px-4 py-3">
                          {log.estado === "SINCRONIZADO" ? (
                            <span className="inline-flex items-center gap-1 text-green-600 bg-green-50 px-2 py-1 rounded text-[10px] font-bold uppercase">
                              <CheckCircleIcon className="w-3 h-3" /> Sincronizado
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-rose-600 bg-rose-50 px-2 py-1 rounded text-[10px] font-bold uppercase">
                              <ExclamationCircleIcon className="w-3 h-3" /> Error
                            </span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Columna Derecha: Parámetros del Punto de Corte */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-slate-800 mb-6 flex items-center gap-2">
                <CalendarIcon className="w-5 h-5 text-blue-500" />
                Punto de Corte
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Fecha/Hora Inicio</label>
                  <input
                    type="datetime-local"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Fecha/Hora Fin</label>
                  <input
                    type="datetime-local"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full p-2.5 border border-slate-200 rounded-lg text-sm text-slate-700 focus:ring-2 focus:ring-blue-500 outline-none"
                  />
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleProcessAndInject}
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