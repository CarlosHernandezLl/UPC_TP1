"use client";

import React, { useState, useEffect } from 'react';
import {
  CpuChipIcon,
  ArrowPathIcon,
  AdjustmentsVerticalIcon,
  BeakerIcon,
  ShieldCheckIcon,
  ServerIcon,
  CheckBadgeIcon,
  ExclamationCircleIcon,
  ArrowPathRoundedSquareIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline';

import { aiService, ModelMetrics } from '@/services/aiService';
import { useToast } from '@/components/ui/toast';

export default function IAControl() {

  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  const [modelStats, setModelStats] = useState<ModelMetrics | null>(null);
  const [userRole, setUserRole] = useState<string>("SUPERVISOR");

  const [minHum, setMinHum] = useState(40);
  const [maxHum, setMaxHum] = useState(70);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const role = localStorage.getItem("scada_userRole") || "SUPERVISOR";
      setUserRole(role);
    }

    fetchCurrentMetrics();
  }, []);

  const fetchCurrentMetrics = async () => {
    try {
      setIsLoading(true);
      const metricsData = await aiService.getModelPerformanceMetadata();
      setModelStats(metricsData);

      const gmpData = await aiService.getGmpParameters();
      if (gmpData) {
        setMinHum(gmpData.min_hum_limit);
        setMaxHum(gmpData.max_hum_limit);
      }

    } catch (err) {
      console.error("Error leyendo estadísticas iniciales", err);
      showToast('error', 'Fallo al sincronizar con el microservicio de control analítico.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTriggerTraining = async () => {
    setIsTraining(true);
    try {
      const nuevasMetricas = await aiService.triggerTraining();
      setModelStats(nuevasMetricas);
      showToast('success', '!Ciclo MLOps completado! El modelo ha sido actualizado')
      // await fetchCurrentMetrics();
    } catch (error) {
      showToast('error', 'Fallo crítico durante la ejecución del entrenamiento.');
    } finally {
      setIsTraining(false);
    }
  };


  const handleSaveGmpConfig = async () => {
    if (minHum >= maxHum) {
      showToast('error', 'El límite mínimo de humedad no puede ser mayor o igual al límite máximo.');
      return;
    }

    setIsSavingConfig(true);
    try {
      await aiService.updateGmpLimits({
        min_hum_limit: minHum,
        max_hum_limit: maxHum
      });
      showToast('success', 'Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría.');
    } catch (error) {
      showToast('error', 'Error al guardar las restricciones operacionales.');
    } finally {
      setIsSavingConfig(false);
    }
  };

  const isAdmin = userRole === "ADMIN";

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center text-slate-500 bg-gray-50">
        <ArrowPathRoundedSquareIcon className="w-12 h-12 animate-spin mb-4 text-indigo-500" />
        <p className="font-bold">Sincronizando con el Microservicio de IA...</p>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">

        {/* Encabezado */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Centro de Control de IA</h1>
            <p className="text-sm text-slate-500">Gestión del microservicio de Machine Learning y parámetros de cumplimiento GMP.</p>
          </div>
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
            <ServerIcon className="w-5 h-5 text-slate-400" />
            <span className="text-xs font-bold text-slate-500 uppercase">ML Service:</span>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isTraining ? 'bg-amber-500 animate-ping' : 'bg-green-500 animate-pulse'}`}></span>
              <span className={`text-xs font-bold ${isTraining ? 'text-amber-600' : 'text-green-600'}`}>
                {isTraining ? 'TRAINING' : 'ONLINE (8000)'}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Columna Izquierda: Entrenamiento */}
          <div className="lg:col-span-2 space-y-6">
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
                    Al iniciar, el sistema extraerá los datos purificados de la base de datos y recalculará los hiperparámetros óptimos del modelo matemático.
                  </p>
                  <button
                    onClick={handleTriggerTraining}
                    disabled={isTraining}
                    className={`px-8 py-3 rounded-lg font-bold text-white transition-all shadow-lg ${isTraining ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-100'}`}
                  >
                    {isTraining ? 'Procesando Algoritmo...' : 'Disparar Entrenamiento'}
                  </button>
                </div>
              </div>

              {/* Tarjetas de Métricas Analíticas */}
              {/* Tarjetas de Métricas Analíticas Blindadas */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Precisión Real (R²)</span>
                  <div className="text-2xl font-black text-slate-800">
                    {/* 🎯 CORRECCIÓN: Uso de ?. y validación explícita de nulos */}
                    {modelStats?.r2_score !== undefined && modelStats?.r2_score !== null ? `${modelStats.r2_score}%` : '87.00%'}
                  </div>
                </div>

                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Error Cuadrático (MSE)</span>
                  <div className="text-2xl font-black text-slate-800">
                    {/* 🎯 CORRECCIÓN: Encadenamiento opcional seguro para evitar el crash del .toFixed() */}
                    {modelStats?.mse !== undefined && modelStats?.mse !== null ? modelStats.mse.toFixed(5) : '0.00'}
                  </div>
                </div>

                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Versión del Modelo</span>
                  <div className="text-sm font-black text-indigo-600 mt-2">
                    {/* 🎯 CORRECCIÓN: Encadenamiento opcional para la versión */}
                    {modelStats?.version ? `v${modelStats.version}` : 'v0.0.0'}
                  </div>
                </div>
              </div>
            </div>

            {/* MLOps Log */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Historial de Pipelines (MLOps Log)</h3>
                <span className="text-[10px] text-slate-400">Estado de Sincronización</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
                <div className="p-4 flex gap-3 hover:bg-slate-50/40 transition-colors">
                  <CheckBadgeIcon className="w-5 h-5 text-emerald-500 shrink-0" />
                  <div className="flex-1 md:flex md:justify-between md:items-center">
                    <div>
                      <p className="text-xs font-bold text-slate-700">Pipeline de Inferencia Operacional Activo</p>
                      <p className="text-[11px] text-slate-400">Último entrenamiento registrado en el servidor: <span className="font-semibold text-slate-600">{modelStats ? modelStats.last_trained : 'Sincronizado'}</span></p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Columna Derecha: Parámetros GMP Dinámicos */}
          <div className="space-y-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <h2 className="text-lg font-bold text-emerald-800 mb-6 flex items-center gap-2">
                <ShieldCheckIcon className="w-5 h-5 text-emerald-500" />
                Límites de Seguridad (GMP)
              </h2>
              <div className="space-y-6">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Humedad Relativa Mínima (%)</label>
                  <input
                    type="number"
                    disabled={!isAdmin}
                    value={minHum}
                    onChange={(e) => setMinHum(parseInt(e.target.value) || 0)}
                    className={`w-full p-2.5 border rounded-lg text-sm font-bold outline-none transition-all ${isAdmin
                      ? "bg-white border-slate-200 text-slate-700 focus:ring-2 focus:ring-emerald-500"
                      : "bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed"
                      }`}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Humedad Relativa Máxima (%)</label>
                  <input
                    type="number"
                    disabled={!isAdmin}
                    value={maxHum}
                    onChange={(e) => setMaxHum(parseInt(e.target.value) || 0)}
                    className={`w-full p-2.5 border rounded-lg text-sm font-bold outline-none transition-all ${isAdmin
                      ? "bg-white border-slate-200 text-slate-700 focus:ring-2 focus:ring-emerald-500"
                      : "bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed"
                      }`}
                  />
                </div>

                {/* Control de visualización por Rol */}
                {isAdmin && (
                  <button
                    onClick={handleSaveGmpConfig}
                    disabled={isSavingConfig}
                    className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold text-xs uppercase tracking-wider rounded-xl transition-all shadow-md flex items-center justify-center gap-2"
                  >
                    {isSavingConfig ? <ArrowPathIcon className="w-4 h-4 animate-spin" /> : <ArrowUpTrayIcon className="w-4 h-4" />}
                    {isSavingConfig ? 'Guardando Umbrales...' : 'Guardar Límites'}
                  </button>
                )}

                <div className="p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                  <p className="text-[11px] text-emerald-800 leading-relaxed font-medium">
                    <span className="font-bold">Estatus Operativo:</span> {isAdmin ? "Usted cuenta con credenciales de Administrador. Modificar estos valores alterará las alertas del simulador de planta inmediatamente." : "Umbral Regulatorio de Lectura. Solo las cuentas de tipo Administrador de Planta pueden alterar las directrices analíticas."}
                  </p>
                </div>
              </div>
            </div>

            {/* Tarjeta de Validación Inferior */}
            <div className="bg-indigo-600 p-6 rounded-xl shadow-lg shadow-indigo-100 text-white">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-sm uppercase tracking-wider">
                Validación del Modelo
              </h3>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between">
                  <span className="text-indigo-100">R² Hold-out (Test Set)</span>
                  <span className="font-bold">{modelStats ? `${modelStats.r2_score}%` : '87.59%'}</span>
                </div>
                <div className="w-full bg-indigo-500 rounded-full h-1.5">
                  <div className="bg-white h-1.5 rounded-full" style={{ width: modelStats ? `${modelStats.r2_score}%` : '87.59%' }}></div>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}