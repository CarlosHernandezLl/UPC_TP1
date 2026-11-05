"use client";

import React, { useEffect, useState } from 'react';
import {
  AdjustmentsHorizontalIcon, CloudIcon, BoltIcon, BeakerIcon,
  ExclamationTriangleIcon, CheckCircleIcon, ArrowPathIcon,
  VariableIcon, HandThumbUpIcon, HandThumbDownIcon
} from '@heroicons/react/24/outline';

// 🚀 CORRECCIÓN 1: Importamos el servicio exclusivo de simulación y su interfaz
import { simulationService, SimulationPredictResponse } from '@/services/simulationService';
import { gmpService } from '@/services/gmpService';
import { useToast } from '@/components/ui/toast';
import { JustificationModal } from '@/components/ui/justification-modal';

export default function Simulator() {
  // Modal Justificacion
  const [isIgnoreModalOpen, setIsIgnoreModalOpen] = useState(false);
  const [isLoggingAction, setIsLoggingAction] = useState(false);

  const { showToast } = useToast();
  const [tempExt, setTempExt] = useState("");
  const [humExt, setHumExt] = useState("");
  const [tempUma, setTempUma] = useState("");
  const [humUma, setHumUma] = useState("");
  const [pwrActual, setPwrActual] = useState("");
  const [tempSala, setTempSala] = useState("");
  const [humSala, setHumSala] = useState("");

  const [presionInyeccion, setPresionInyeccion] = useState("");

  const [setpoint, setSetpoint] = useState("");

  const [isCalculating, setIsCalculating] = useState(false);
  const [result, setResult] = useState<SimulationPredictResponse | null>(null);
  const [actionLogged, setActionLogged] = useState(false);
  const [minHumLimit, setMinHumLimit] = useState(40);
  const [maxHumLimit, setMaxHumLimit] = useState(55);

  useEffect(() => {
    const fetchActiveGmpLimits = async () => {
      try {
        const gmpData = await gmpService.getGmpParameters();
        if (gmpData.min_hum_limit) setMinHumLimit(gmpData.min_hum_limit);
        if (gmpData.max_hum_limit) setMaxHumLimit(gmpData.max_hum_limit);
      } catch (err) {
        console.error("⚠️ Advertencia: No se pudo conectar con los umbrales dinámicos. Usando fallback de seguridad.", err);
      }
    };
    fetchActiveGmpLimits();
  }, []);

  // Metadatos de cada variable: etiqueta para mensajes y unidad del rango
  const FIELD_META: Record<string, { label: string; unit: string }> = {
    tempExt: { label: "Temp. Exterior", unit: "°C" },
    humExt: { label: "Humedad Ext.", unit: "% HR" },
    tempUma: { label: "Temp. UMA", unit: "°C" },
    humUma: { label: "Hum. UMA", unit: "% HR" },
    presionInyeccion: { label: "Presión Inyección", unit: "Pa" },
    pwrActual: { label: "Potencia", unit: "%" },
    humSala: { label: "Humedad Sala Actual", unit: "% HR" },
    setpoint: { label: "Humedad Sala Objetivo", unit: "% HR" },
    tempSala: { label: "Temp. Sala", unit: "°C" },
  };

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const setFieldError = (key: string, message: string | null) => {
    setFieldErrors((prev) => {
      const next = { ...prev };
      if (message) next[key] = message;
      else delete next[key];
      return next;
    });
  };

  const handleNumberChange = (
    key: string,
    value: string,
    setter: React.Dispatch<React.SetStateAction<string>>,
    min: number,
    max: number
  ) => {
    if (value === "") {
      setter("");
      setFieldError(key, null);
      return;
    }

    const num = parseFloat(value);
    if (isNaN(num)) return;

    if (num >= min && num <= max) {
      setter(value);
      setFieldError(key, null);
    } else {
      // El valor se rechaza, pero se explica el motivo y el rango admitido
      const meta = FIELD_META[key];
      setFieldError(key, `Valor fuera de rango. ${meta.label}: de ${min} a ${max} ${meta.unit}.`);
    }
  };

  const renderInput = (
    key: string,
    value: string,
    setter: React.Dispatch<React.SetStateAction<string>>,
    min: number,
    max: number,
    cls: string
  ) => {
    const error = fieldErrors[key];
    const errCls = error ? " border-rose-500 ring-1 ring-rose-400 bg-rose-50/40" : "";
    return (
      <>
        <input
          id={`field-${key}`}
          type="number" step="0.5" min={min} max={max} placeholder=""
          value={value}
          onChange={(e) => handleNumberChange(key, e.target.value, setter, min, max)}
          aria-invalid={!!error}
          className={cls + errCls}
        />
        {error && <p className="text-[10px] text-rose-600 font-bold mt-1">{error}</p>}
      </>
    );
  };

  // Mensaje según qué grupo de variables falta (HU0006-2, HU0007-2, HU0008-2); en cualquier otro caso, el genérico
  const GENERIC_MISSING_MSG = 'Por favor, llene todas las variables de operación antes de consultar al Gemelo Digital';
  const MISSING_NAMES: Record<string, string> = {
    tempExt: "Temperatura externa", humExt: "Humedad externa",
    tempUma: "Temperatura de la UMA", humUma: "Humedad de la UMA", presionInyeccion: "Presión de la UMA",
    pwrActual: "Potencia", humSala: "Humedad actual de la sala", setpoint: "Humedad objetivo de la sala",
    tempSala: "Temperatura de la sala",
  };
  // Grupos de variables: si falta el grupo completo se nombra el grupo; si no, cada variable por separado
  const MISSING_GROUPS: { keys: string[]; name: string; huMsg?: string }[] = [
    { keys: ["tempExt", "humExt"], name: "Temperatura y Humedad externa",
      huMsg: 'Por favor, llene las variables de Temperatura y Humeda externa antes de consultar al Gemelo Digital' },
    { keys: ["tempUma", "humUma", "presionInyeccion"], name: "Temperatura, Humedad y Presión de la UMA",
      huMsg: 'Por favor, llene las variables de Temperatura, Humedad y Presion de la UMA antes de consultar al Gemelo Digital' },
    { keys: ["humSala", "tempSala"], name: "Humedad Sala Actual (HR %) y Temp. Sala (°C)" },
  ];
  const buildMissingMessage = (missing: string[], totalRequired: number): string => {
    if (missing.length === totalRequired) return GENERIC_MISSING_MSG;
    const parts: string[] = [];
    const used = new Set<string>();
    let single: (typeof MISSING_GROUPS)[number] | undefined;
    for (const g of MISSING_GROUPS) {
      if (g.keys.every((k) => missing.includes(k))) { parts.push(g.name); g.keys.forEach((k) => used.add(k)); single = g; }
    }
    missing.filter((k) => !used.has(k)).forEach((k) => parts.push(MISSING_NAMES[k]));
    // Un único grupo completo conserva la redacción de las HU (HU0006-2, HU0007-2)
    if (parts.length === 1 && single?.huMsg) return single.huMsg;
    const list = parts.length === 1 ? parts[0] : `${parts.slice(0, -1).join(", ")} y ${parts[parts.length - 1]}`;
    const isPlural = parts.length > 1 || (single !== undefined && parts.length === 1);
    return `Por favor, llene ${isPlural ? "las variables de" : "la variable de"} ${list} antes de consultar al Gemelo Digital`;
  };

  const handleSimulate = async () => {
    const required: [string, string][] = [
      ["tempExt", tempExt], ["humExt", humExt], ["tempUma", tempUma], ["humUma", humUma],
      ["presionInyeccion", presionInyeccion], ["pwrActual", pwrActual], ["humSala", humSala],
      ["setpoint", setpoint], ["tempSala", tempSala],
    ];
    const missing = required.filter(([, v]) => v === "").map(([k]) => k);
    if (missing.length > 0) {
      // Un resultado previo ya no es válido: reiniciamos la card al estado inicial
      setResult(null);
      setActionLogged(false);

      const errors: Record<string, string> = {};
      missing.forEach((k) => { errors[k] = `Campo obligatorio: ${FIELD_META[k].label}.`; });
      setFieldErrors(errors);
      document.getElementById(`field-${missing[0]}`)?.focus();

      showToast('error', buildMissingMessage(missing, required.length));
      return;
    }
    setFieldErrors({});

    setIsCalculating(true);
    setResult(null);
    setActionLogged(false);

    try {
      const data = await simulationService.predictPower({
        outdoor_temp: parseFloat(tempExt),
        outdoor_rh: parseFloat(humExt),
        ahu_temp: parseFloat(tempUma),
        ahu_rh: parseFloat(humUma),
        current_power: parseFloat(pwrActual),
        current_room_rh: parseFloat(humSala),
        room_temp: parseFloat(tempSala),              // 🚀 NUEVO
        injection_pressure: parseFloat(presionInyeccion), // 🚀 NUEVO
        target_setpoint: parseFloat(setpoint)
      });

      setResult(data);
    } catch (error) {
      showToast('error', 'Error de conexión con el motor del Gemelo Digital.');
      console.error(error);
    } finally {
      setIsCalculating(false);
    }
  };

  const handleApplyRecommendation = async () => {
    if (!result) return;
    try {
      // 🚀 CORRECCIÓN 4: Payload de auditoría en inglés técnico estandarizado
      await simulationService.logOperatorAction({
        outdoor_temp: parseFloat(tempExt),
        outdoor_rh: parseFloat(humExt),
        ahu_temp: parseFloat(tempUma),
        ahu_rh: parseFloat(humUma),
        current_room_rh: parseFloat(humSala),
        room_temp: parseFloat(tempSala),
        injection_pressure: parseFloat(presionInyeccion),
        target_setpoint: parseFloat(setpoint),
        current_power: parseFloat(pwrActual),
        recommended_power: result.potencia_recomendada,
        applied_power: result.potencia_recomendada,
        action: "RECOMMENDATION_APPLIED",
        justification: "N/A"
      });
      setActionLogged(true);
      showToast('success', `Recomendación Aplicada. Ajuste del ${result.potencia_recomendada}%. Transacción cifrada en Audit Trail.`);
    } catch {
      showToast('error', 'No se pudo registrar la telemetría de la acción.');
    }
  };

  const handleIgnoreRecommendation = () => {
    if (!result) return;
    setIsIgnoreModalOpen(true);
  };

  const handleConfirmIgnore = async (motivo: string) => {
    if (!result) return;
    try {
      setIsLoggingAction(true);

      await simulationService.logOperatorAction({
        outdoor_temp: parseFloat(tempExt),
        outdoor_rh: parseFloat(humExt),
        ahu_temp: parseFloat(tempUma),
        ahu_rh: parseFloat(humUma),
        current_room_rh: parseFloat(humSala),
        room_temp: parseFloat(tempSala),
        injection_pressure: parseFloat(presionInyeccion),
        target_setpoint: parseFloat(setpoint),
        current_power: parseFloat(pwrActual),
        recommended_power: result.potencia_recomendada,
        applied_power: parseFloat(pwrActual),
        action: "RECOMMENDATION_OVERRIDDEN",
        justification: motivo
      });

      setActionLogged(true);
      setIsIgnoreModalOpen(false);
      showToast('success', 'Descarte operativo registrado con éxito junto a su sustento técnico.');
    } catch {
      showToast('error', 'Fallo del servidor al intentar registrar la bitácora de descarte.');
    } finally {
      setIsLoggingAction(false);
    }
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col mb-8">
          <h1 className="text-2xl font-bold text-slate-800">Simulador de Optimización Energética</h1>
          <p className="text-slate-500 text-sm">Ingrese las condiciones actuales para obtener la recomendación predictiva.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3">

          {/* Columna Izquierda: Entradas Manuales */}
          <div className="space-y-6 lg:col-span-3">
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
                      {renderInput("tempExt", tempExt, setTempExt, 0, 50, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Ext. (HR %)</label>
                      {renderInput("humExt", humExt, setHumExt, 0, 100, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                  </div>
                </div>

                {/* Grupo: Condiciones UMA */}
                <div className="space-y-4">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <VariableIcon className="w-4 h-4" /> Entrada Aire (UMA)
                  </h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Temp. UMA (°C)</label>
                      {renderInput("tempUma", tempUma, setTempUma, 0, 50, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Hum. UMA (HR %)</label>
                      {renderInput("humUma", humUma, setHumUma, 0, 100, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Presión Inyección (Pa)</label>
                      {renderInput("presionInyeccion", presionInyeccion, setPresionInyeccion, 0, 1000, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>

                  </div>
                </div>

                {/* Grupo: Datos de Sala y Secador */}
                <div className="space-y-4 md:col-span-2 pt-4 border-t border-slate-50">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <BeakerIcon className="w-4 h-4" /> Estado de la Sala
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Potencia Estimada (%)</label>
                      {renderInput("pwrActual", pwrActual, setPwrActual, 0, 100, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Sala Actual (HR %)</label>
                      {renderInput("humSala", humSala, setHumSala, 0, 100, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Humedad Sala Objetivo (HR %)</label>
                      {renderInput("setpoint", setpoint, setSetpoint, 0, 100, "w-full p-2 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 border-2 border-blue-200 bg-blue-50/50 font-bold text-blue-800")}
                    </div>
                    <div>
                      <label className="block text-[11px] font-bold text-slate-500 mb-1">Temp. Sala (°C)</label>
                      {renderInput("tempSala", tempSala, setTempSala, 0, 50, "w-full p-2 border border-slate-200 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium")}
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
                <ExclamationTriangleIcon className="w-8 h-8 text-rose-500 shrink-0" />
                <div>
                  <h4 className="text-rose-800 font-bold text-sm uppercase">Alerta de Riesgo GMP</h4>
                  <p className="text-rose-600 text-[10px] font-black uppercase tracking-wider">Alerta de incumplimiento de límites</p>
                  <p className="text-rose-700 text-xs mt-1">
                    El setpoint solicitado, o las condiciones de humedad logradas por el modelo,
                    apuntan a una violación del marco regulatorio estricto
                    de la sala (<span className="font-black text-rose-900">
                      Rango permitido: {minHumLimit}% a {maxHumLimit}% HR</span>).
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Columna Derecha: Resultado de Recomendación */}
          <div className="space-y-6 mt-6 lg:mt-0">
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
                        <span className="text-blue-500">✨</span> Explicabilidad del Modelo
                      </p>
                      <p className="text-xs text-slate-600 italic">
                        &quot;{result.explicacion_gemini}&quot;
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
                            <HandThumbUpIcon className="w-4 h-4" /> Sí, aplicada
                          </button>

                          <button
                            onClick={handleIgnoreRecommendation}
                            className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-600 py-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-colors"
                          >
                            <HandThumbDownIcon className="w-4 h-4" /> Ignorar
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

      <JustificationModal
        isOpen={isIgnoreModalOpen}
        onClose={() => setIsIgnoreModalOpen(false)}
        onConfirm={handleConfirmIgnore}
        isSubmitting={isLoggingAction}
      />

    </div>
  );
}