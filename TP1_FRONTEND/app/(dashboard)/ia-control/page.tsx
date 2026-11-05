"use client";

import React, { useState, useEffect } from 'react';
import {
  CpuChipIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  ServerIcon,
  CheckBadgeIcon,
  ExclamationCircleIcon,
  ArrowPathRoundedSquareIcon,
  ArrowUpTrayIcon
} from '@heroicons/react/24/outline';

// 🚀 CORRECCIÓN 1: Importamos los 2 servicios especializados en lugar del monolito
import { mlopsService, ModelMetrics, TrainingLogEntry } from '@/services/mlopsService';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { gmpService } from '@/services/gmpService';
import { useToast } from '@/components/ui/toast';

const FEATURE_LABELS: Record<string, string> = {
  dryer_power: 'Potencia del secador',
  outdoor_temp: 'Temp. exterior',
  outdoor_w: 'Humedad abs. exterior',
  ahu_temp: 'Temp. UMA',
  ahu_w: 'Humedad abs. UMA',
  injection_pressure: 'Presión de inyección',
};

export default function IAControl() {

  const { showToast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [isTraining, setIsTraining] = useState(false);
  const [isSavingConfig, setIsSavingConfig] = useState(false);

  const [modelStats, setModelStats] = useState<ModelMetrics | null>(null);
  const [trainingLog, setTrainingLog] = useState<TrainingLogEntry[]>([]);
  const [userRole, setUserRole] = useState<string>("SUPERVISOR");

  const [minHum, setMinHum] = useState(40);
  const [maxHum, setMaxHum] = useState(70);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const role = localStorage.getItem("scada_userRole") || "SUPERVISOR";
      setUserRole(role);
    }

    fetchCurrentMetrics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchCurrentMetrics = async () => {
    try {
      setIsLoading(true);

      // 🚀 CORRECCIÓN 2: Separación de llamadas a los servicios respectivos
      const metricsData = await mlopsService.getActiveModelMetrics();
      setModelStats(metricsData);

      try {
        setTrainingLog(await mlopsService.getTrainingLog());
      } catch (e) {
        console.error("No se pudo leer el historial de entrenamiento", e);
      }

      const gmpData = await gmpService.getGmpParameters();
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
      // 🚀 CORRECCIÓN 3: Llamamos a mlopsService y refrescamos la UI
      await mlopsService.triggerRetraining();
      showToast('success', '¡Ciclo MLOps completado! El modelo ha sido actualizado.');

      // Volvemos a consultar para que las tarjetas se actualicen con el nuevo Champion
      await fetchCurrentMetrics();
    } catch {
      showToast('error', 'Fallo crítico en el pipeline MLOps');
      // El motivo del fallo queda registrado: refrescamos el historial
      try { setTrainingLog(await mlopsService.getTrainingLog()); } catch { /* sin acción */ }
    } finally {
      setIsTraining(false);
    }
  };

  // Los límites de humedad deben ser un porcentaje físicamente posible (0–100): lo demás no se digita (HU0004-1)
  const blockInvalidKeys = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (['-', '+', 'e', 'E'].includes(e.key)) e.preventDefault();
  };

  const handleLimitChange = (raw: string, setter: React.Dispatch<React.SetStateAction<number>>) => {
    const value = raw === "" ? 0 : parseFloat(raw);
    if (isNaN(value) || value < 0 || value > 100) return;
    setter(value);
  };

  const handleSaveGmpConfig = async () => {
    if (minHum >= maxHum) {
      showToast('error', 'El límite mínimo de humedad no puede ser mayor o igual al límite máximo.');
      return;
    }

    setIsSavingConfig(true);
    try {
      // 🚀 CORRECCIÓN 4: Llamamos al servicio exclusivo de normativas
      await gmpService.updateGmpLimits({
        min_hum_limit: minHum,
        max_hum_limit: maxHum
      });
      showToast('success', 'Umbrales regulatorios actualizados. Cambio firmado en la pista de auditoría.');
    } catch {
      showToast('error', 'Error al guardar las restricciones operacionales.');
    } finally {
      setIsSavingConfig(false);
    }
  };

  const isAdmin = userRole === "ADMIN";

  const shapData = (modelStats?.feature_importance ?? []).map((f) => ({
    name: FEATURE_LABELS[f.feature] ?? f.feature,
    shap: f.shap,
  }));

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
                {isTraining ? 'TRAINING' : 'ONLINE'}
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

              {/* Tarjetas de Métricas Analíticas Blindadas */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Precisión Real (R²)</span>
                  <div className="text-2xl font-black text-slate-800">
                    {modelStats?.r2_score !== undefined && modelStats?.r2_score !== null ? `${modelStats.r2_score}%` : '—'}
                  </div>
                </div>

                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  {/* 🚀 CORRECCIÓN 5: Actualizamos el título a RMSE porque ahora pasamos la raíz del error */}
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Error Promedio (RMSE)</span>
                  <div className="text-2xl font-black text-slate-800">
                    {/* 🚀 CORRECCIÓN 6: Usamos rmse según el nuevo esquema del ModelMetrics */}
                    {modelStats?.rmse !== undefined && modelStats?.rmse !== null ? modelStats.rmse.toFixed(5) : '0.00'}
                  </div>
                  {modelStats?.rmse !== undefined && modelStats?.rmse !== null && (
                    <div className="text-[10px] font-bold text-slate-400 mt-1">MSE: {(modelStats.rmse ** 2).toFixed(5)}</div>
                  )}
                </div>

                <div className="p-4 border border-slate-200 rounded-lg bg-white shadow-sm">
                  <span className="block text-[10px] font-bold text-slate-400 uppercase mb-1">Versión del Modelo</span>
                  <div className="text-sm font-black text-indigo-600 mt-2">
                    {/* 🚀 CORRECCIÓN 7: Usamos version_tag según el registro de la BD */}
                    {modelStats?.version_tag ? modelStats.version_tag : 'v0.0.0'}
                  </div>
                </div>
              </div>
            </div>

            {/* MLOps Log */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-4 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Historial de Entrenamiento</h3>
                <span className="text-[10px] text-slate-400">Estado de Sincronización</span>
              </div>
              <div className="divide-y divide-slate-100 max-h-64 overflow-y-auto">
                {trainingLog.length === 0 ? (
                  <div className="p-4 text-xs text-slate-400">
                    Sin entrenamientos registrados. Último modelo en producción: <span className="font-semibold text-slate-600">{modelStats ? modelStats.trained_at : 'Sincronizado'}</span>
                  </div>
                ) : (
                  trainingLog.map((entry) => (
                    <div key={entry.id} className="p-4 flex gap-3 hover:bg-slate-50/40 transition-colors">
                      {entry.status === 'SUCCESS' ? (
                        <CheckBadgeIcon className="w-5 h-5 text-emerald-500 shrink-0" />
                      ) : (
                        <ExclamationCircleIcon className="w-5 h-5 text-rose-500 shrink-0" />
                      )}
                      <div className="flex-1">
                        <p className="text-xs font-bold text-slate-700">
                          {entry.status === 'SUCCESS' ? 'Entrenamiento exitoso' : entry.status === 'REJECTED' ? 'Entrenamiento rechazado' : 'Entrenamiento fallido'}
                          <span className="ml-2 text-[10px] font-medium text-slate-400">{entry.timestamp} · {entry.user}</span>
                        </p>
                        <p className="text-[11px] text-slate-500 break-words">{entry.detail}</p>
                      </div>
                    </div>
                  ))
                )}
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
                    type="number" min={0} max={100} step="0.1"
                    disabled={!isAdmin}
                    value={minHum}
                    onKeyDown={blockInvalidKeys}
                    onChange={(e) => handleLimitChange(e.target.value, setMinHum)}
                    className={`w-full p-2.5 border rounded-lg text-sm font-bold outline-none transition-all ${isAdmin
                      ? "bg-white border-slate-200 text-slate-700 focus:ring-2 focus:ring-emerald-500"
                      : "bg-slate-50 border-slate-200 text-slate-400 cursor-not-allowed"
                      }`}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Humedad Relativa Máxima (%)</label>
                  <input
                    type="number" min={0} max={100} step="0.1"
                    disabled={!isAdmin}
                    value={maxHum}
                    onKeyDown={blockInvalidKeys}
                    onChange={(e) => handleLimitChange(e.target.value, setMaxHum)}
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
                  <span className="text-indigo-100">R² Validación (LOSO)</span>
                  <span className="font-bold">{modelStats ? `${modelStats.r2_score}%` : '—'}</span>
                </div>
                <div className="w-full bg-indigo-500 rounded-full h-1.5">
                  <div className="bg-white h-1.5 rounded-full" style={{ width: modelStats ? `${modelStats.r2_score}%` : '—' }}></div>
                </div>

                <div className="mt-3 p-3 bg-white rounded-lg text-slate-800">
                  <div className="font-bold uppercase tracking-wider text-[11px] mb-1 text-slate-700">Impacto de variables (SHAP)</div>
                  <p className="text-slate-500 text-[10px] leading-snug mb-2">
                    Contribución media |SHAP| de cada variable a la humedad de sala predicha (g/kg).
                  </p>
                  {shapData.length === 0 ? (
                    <div className="p-3 text-center text-[11px] text-slate-400 bg-slate-50 rounded-lg border border-slate-100">
                      Sin análisis SHAP aún. Se genera al ejecutar un entrenamiento.
                    </div>
                  ) : (
                    <div style={{ height: shapData.length * 34 + 30 }} className="w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={shapData} layout="vertical" margin={{ top: 0, right: 10, bottom: 15, left: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                          <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 10 }} label={{ value: '|SHAP| medio (g/kg)', position: 'insideBottom', offset: -8, fill: '#64748b', fontSize: 10 }} />
                          <YAxis type="category" dataKey="name" width={110} axisLine={false} tickLine={false} tick={{ fill: '#475569', fontSize: 10 }} />
                          <Tooltip cursor={{ fill: '#f8fafc' }} formatter={(v) => [`${Number(v).toFixed(4)} g/kg`, 'Impacto']} />
                          <Bar dataKey="shap" radius={[0, 4, 4, 0]}>
                            {shapData.map((_, i) => (
                              <Cell key={i} fill={i === 0 ? '#4f46e5' : '#a5b4fc'} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}