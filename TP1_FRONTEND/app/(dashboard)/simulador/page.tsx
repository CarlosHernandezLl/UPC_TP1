"use client";

import React, { useState } from 'react';
import {
  AdjustmentsHorizontalIcon, CloudIcon, BoltIcon, BeakerIcon,
  ExclamationTriangleIcon, CheckCircleIcon, ArrowPathIcon,
  VariableIcon, HandThumbUpIcon, HandThumbDownIcon
} from '@heroicons/react/24/outline';

import { aiService, SimulationResponse } from '@/services/aiService';

export default function Simulator() {
  // CORRECCIÓN: Todos los estados inician estrictamente vacíos para evitar confusiones
  const [tempExt, setTempExt] = useState("");
  const [humExt, setHumExt] = useState("");
  const [tempUma, setTempUma] = useState("");
  const [humUma, setHumUma] = useState("");
  const [pwrActual, setPwrActual] = useState("");
  const [humSala, setHumSala] = useState("");
  const [setpoint, setSetpoint] = useState(""); // Ajustado a ""

  const [isCalculating, setIsCalculating] = useState(false);
  const [result, setResult] = useState<SimulationResponse | null>(null);
  const [actionLogged, setActionLogged] = useState(false);

  // Función de validación y filtro numérico en tiempo real
  const handleNumberChange = (
    value: string,
    setter: React.Dispatch<React.SetStateAction<string>>,
    min: number,
    max: number
  ) => {
    if (value === "") {
      setter("");
      return;
    }

    const num = parseFloat(value);
    if (isNaN(num)) return;

    if (num >= min && num <= max) {
      setter(value);
    }
  };

  const handleSimulate = async () => {
    if (!tempExt || !humExt || !tempUma || !humUma || !pwrActual || !humSala || !setpoint) {
      alert("Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital.");
      return;
    }

    setIsCalculating(true);
    setResult(null);
    setActionLogged(false);

    try {
      const data = await aiService.predictPower({
        temp_ext: parseFloat(tempExt),
        hum_ext: parseFloat(humExt),
        temp_uma: parseFloat(tempUma),
        hum_uma: parseFloat(humUma),
        potencia_actual: parseFloat(pwrActual),
        hum_sala_actual: parseFloat(humSala),
        setpoint_humedad: parseFloat(setpoint)
      });

      setResult(data);
    } catch (error) {
      alert("Error de conexión con el motor del Gemelo Digital.");
      console.error(error);
    } finally {
      setIsCalculating(false);
    }
  };

  const handleApplyRecommendation = async () => {
    if (!result) return;
    try {
      await aiService.logOperatorAction(result.potencia_recomendada, "APLICADA");
      setActionLogged(true);
    } catch (error) {
      alert("No se pudo registrar la auditoría de la acción.");
    }
  };

  const handleIgnoreRecommendation = async () => {
    if (!result) return;
    try {
      await aiService.logOperatorAction(result.potencia_recomendada, "IGNORADA");
      setActionLogged(true);
    } catch (error) {
      alert("No se pudo registrar la auditoría de la acción.");
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Simulador de Optimización Energética</h1>
          <p className="text-slate-500 text-sm">Ingrese las condiciones actuales para obtener la recomendación predictiva.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* Columna Izquierda: Entradas Manuales */}
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
                      <input
                        type="number" step="0.1" min="-10" max="60" placeholder="Ej: 21.5"
                        value={tempExt}
                        onChange={(e) => handleNumberChange(e.target.value, setTempExt, -10, 60)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Ext. (%)</label>
                      <input
                        type="number" step="0.1" min="0" max="100" placeholder="Ej: 78"
                        value={humExt}
                        onChange={(e) => handleNumberChange(e.target.value, setHumExt, 0, 100)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
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
                      <input
                        type="number" step="0.1" min="-10" max="60" placeholder="Ej: 23.2"
                        value={tempUma}
                        onChange={(e) => handleNumberChange(e.target.value, setTempUma, -10, 60)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Hum. UMA (%)</label>
                      <input
                        type="number" step="0.1" min="0" max="100" placeholder="Ej: 42"
                        value={humUma}
                        onChange={(e) => handleNumberChange(e.target.value, setHumUma, 0, 100)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
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
                      <input
                        type="number" step="0.1" min="0" max="100" placeholder="Ej: 80"
                        value={pwrActual}
                        onChange={(e) => handleNumberChange(e.target.value, setPwrActual, 0, 100)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Sala Actual (%)</label>
                      <input
                        type="number" step="0.1" min="0" max="100" placeholder="Ej: 52.4"
                        value={humSala}
                        onChange={(e) => handleNumberChange(e.target.value, setHumSala, 0, 100)}
                        className="w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
                      />
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Setpoint Objetivo (%)</label>
                      <input
                        type="number" step="0.1" min="0" max="100" placeholder="Ej: 50"
                        value={setpoint}
                        onChange={(e) => handleNumberChange(e.target.value, setSetpoint, 0, 100)}
                        className="w-full p-2 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 border-2 border-blue-200 bg-blue-50/50 font-bold text-blue-800"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex justify-end">
                <button
                  onClick={handleSimulate}
                  disabled={isCalculating}
                  className="bg-slate-900 text-white px-8 py-3 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-800 transition-all shadow-lg shadow-slate-200 disabled:bg-slate-400"
                >
                  {isCalculating ? <ArrowPathIcon className="w-5 h-5 animate-spin" /> : <BoltIcon className="w-5 h-5" />}
                  {isCalculating ? 'Consultando Gemelo Digital...' : 'Generar Recomendación'}
                </button>
              </div>
            </div>

            {/* Alerta de Riesgo (Dinámica) */}
            {result?.alerta_gmp && (
              <div className="bg-rose-50 border border-rose-200 p-4 rounded-xl flex gap-4 animate-pulse">
                <ExclamationTriangleIcon className="w-8 h-8 text-rose-500 flex-shrink-0" />
                <div>
                  <h4 className="text-rose-800 font-bold text-sm uppercase">Alerta de Riesgo GMP</h4>
                  <p className="text-rose-700 text-xs mt-1">El setpoint solicitado, o las condiciones termodinámicas actuales, apuntan a un posible incumplimiento del límite del 55% de humedad relativa.</p>
                </div>
              </div>
            )}
          </div>

          {/* Columna Derecha: Resultado de Recomendación */}
          <div className="space-y-6">
            <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200 text-center relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-2 bg-blue-600"></div>
              <h2 className="text-slate-400 font-bold text-xs uppercase tracking-widest mb-4">Potencia Recomendada IA</h2>

              {result ? (
                <div className="space-y-4 animate-fadeIn">
                  <div className="text-6xl font-black text-slate-900">
                    {result.potencia_recomendada}%
                  </div>

                  {result.ahorro_estimado_pct > 0 ? (
                    <div className="text-sm font-bold text-emerald-600 bg-emerald-50 py-2 rounded-lg border border-emerald-100">
                      Ahorro Estimado: {result.ahorro_estimado_pct}%
                    </div>
                  ) : (
                    <div className="text-sm font-bold text-slate-500 bg-slate-50 py-2 rounded-lg border border-slate-100">
                      Ajuste por estabilidad
                    </div>
                  )}

                  {/* CAJA DE EXPLICABILIDAD (IA GENERATIVA) */}
                  {result.explicacion_gemini && (
                    <div className="mt-4 p-3 bg-blue-50/50 rounded-xl border border-blue-100 text-left">
                      <p className="text-[10px] font-black text-blue-500 uppercase mb-1 flex items-center gap-1">
                        <SparklesIcon /> Explicabilidad del Modelo
                      </p>
                      <p className="text-xs text-slate-600 italic">
                        "{result.explicacion_gemini}"
                      </p>
                    </div>
                  )}

                  <div className="pt-6 border-t border-slate-100">
                    {!actionLogged ? (
                      <>
                        <p className="text-xs text-slate-500 mb-4 font-medium">¿Aplicó este ajuste en el PLC físico?</p>

                        <div className="flex gap-2">
                          <button
                            onClick={handleApplyRecommendation}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors shadow-md"
                          >
                            <HandThumbUpIcon className="w-4 h-4" /> SÍ, APLICADA
                          </button>

                          <button
                            onClick={handleIgnoreRecommendation}
                            className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-600 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors"
                          >
                            <HandThumbDownIcon className="w-4 h-4" /> IGNORAR
                          </button>
                        </div>
                      </>
                    ) : (
                      <div className="bg-emerald-50 text-emerald-600 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 border border-emerald-200">
                        <CheckCircleIcon className="w-5 h-5" />
                        AUDITORÍA REGISTRADA
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="py-12 space-y-3">
                  <BoltIcon className="w-12 h-12 text-slate-200 mx-auto" />
                  <p className="text-slate-400 text-xs italic font-medium px-4">Esperando entrada de datos para procesar con XGBoost...</p>
                </div>
              )}
            </div>

            {/* Audit Log Rápido (Feedback visual) */}
            {actionLogged && (
              <div className="bg-white p-6 rounded-xl shadow-sm border border-emerald-200 animate-fadeIn">
                <h3 className="text-xs font-bold text-emerald-700 uppercase mb-2 flex items-center gap-2">
                  <CheckCircleIcon className="w-4 h-4" /> Trazabilidad GMP
                </h3>
                <p className="text-[10px] text-slate-500">
                  Su decisión ha sido cifrada y almacenada en el Audit Trail bajo el ID de su sesión actual para cumplimiento normativo (FDA 21 CFR Part 11).
                </p>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

function SparklesIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-3 h-3">
      <path fillRule="evenodd" d="M9 4.5a.75.75 0 01.721.544l.813 2.846a3.75 3.75 0 002.576 2.576l2.846.813a.75.75 0 010 1.442l-2.846.813a3.75 3.75 0 00-2.576 2.576l-.813 2.846a.75.75 0 01-1.442 0l-.813-2.846a3.75 3.75 0 00-2.576-2.576l-2.846-.813a.75.75 0 010-1.442l2.846-.813A3.75 3.75 0 007.466 7.89l.813-2.846A.75.75 0 019 4.5zM18 1.5a.75.75 0 01.728.568l.258 1.036c.236.94.97 1.674 1.91 1.91l1.036.258a.75.75 0 010 1.456l-1.036.258c-.94.236-1.674.97-1.91 1.91l-.258 1.036a.75.75 0 01-1.456 0l-.258-1.036a2.625 2.625 0 00-1.91-1.91l-1.036-.258a.75.75 0 010-1.456l1.036-.258a2.625 2.625 0 001.91-1.91l.258-1.036A.75.75 0 0118 1.5zM16.5 15a.75.75 0 01.712.513l.394 1.183c.15.447.5.799.948.948l1.183.395a.75.75 0 010 1.422l-1.183.395c-.447.15-.799.5-.948.948l-.395 1.183a.75.75 0 01-1.422 0l-.395-1.183a1.5 1.5 0 00-.948-.948l-1.183-.395a.75.75 0 010-1.422l1.183-.395c.447-.15.799-.5.948-.948l.395-1.183A.75.75 0 0116.5 15z" clipRule="evenodd" />
    </svg>
  );
}