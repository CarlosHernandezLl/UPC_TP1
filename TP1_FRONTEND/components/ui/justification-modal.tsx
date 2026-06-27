"use client";

import React, { useState } from 'react';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface JustificationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (justificacion: string) => void;
    isSubmitting: boolean;
}

export function JustificationModal({ isOpen, onClose, onConfirm, isSubmitting }: JustificationModalProps) {
    const [text, setText] = useState("");
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (text.trim().length < 10) {
            setError("Por normativa GxP, debe ingresar una justificación técnica detallada (mínimo 10 caracteres).");
            return;
        }
        setError(null);
        onConfirm(text.trim());
        setText(""); 
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-fadeIn">
            <div className="bg-white w-full max-w-md p-8 rounded-3xl shadow-2xl relative border border-slate-100">

                {/* Botón Cerrar */}
                <button
                    onClick={onClose}
                    disabled={isSubmitting}
                    className="absolute top-6 right-6 text-slate-400 hover:text-slate-800 transition-colors disabled:opacity-50"
                >
                    <XMarkIcon className="w-6 h-6" />
                </button>

                {/* Encabezado de Advertencia */}
                <div className="flex items-center gap-3 mb-4 text-amber-600 bg-amber-50 p-3 rounded-xl border border-amber-100">
                    <ExclamationTriangleIcon className="w-6 h-6 shrink-0" />
                    <h2 className="text-sm font-black uppercase tracking-wider">Control de Desvío Operacional</h2>
                </div>

                <p className="text-slate-500 text-xs mb-6 font-medium leading-relaxed">
                    Está a punto de ignorar la recomendación del Gemelo Digital. Ingrese el sustento técnico para la pista de auditoría interna (**FDA 21 CFR Part 11**).
                </p>

                {/* Formulario */}
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-[10px] font-black text-slate-400 uppercase mb-2 tracking-wider">
                            Justificación Técnica Obligatoria
                        </label>
                        <textarea
                            required
                            rows={4}
                            disabled={isSubmitting}
                            placeholder="Ej: Se detectó mantenimiento correctivo en ductos de inyección o riesgo de condensación térmica por humedad externa..."
                            value={text}
                            onChange={(e) => {
                                setText(e.target.value);
                                if (error) setError(null);
                            }}
                            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-none focus:ring-2 focus:ring-blue-500 font-semibold text-slate-700 placeholder-slate-400 resize-none transition-all disabled:opacity-60"
                        />
                        {error && (
                            <p className="text-[10px] text-rose-600 font-bold mt-1 animate-pulse">⚠️ {error}</p>
                        )}
                    </div>

                    {/* Botones de Acción */}
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={isSubmitting}
                            className="flex-1 py-3 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
                        >
                            Cancelar
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting}
                            className="flex-1 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg transition-colors disabled:bg-slate-400"
                        >
                            {isSubmitting ? "Registrando..." : "Confirmar Descarte"}
                        </button>
                    </div>
                </form>

            </div>
        </div>
    );
}