"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { CheckBadgeIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

interface ToastMessage {
  type: 'success' | 'error';
  message: string;
}

interface ToastContextType {
  showToast: (type: 'success' | 'error', message: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastMessage | null>(null);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    
    setTimeout(() => {
      setToast(null);
    }, 5000);
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}

      {/* RENDERIZADO DEL CARD FLOTANTE GLOBAL */}
      {toast && (
        <div 
          className={`fixed bottom-6 right-6 z-50 max-w-sm w-full bg-white p-4 rounded-xl shadow-2xl border flex gap-3 transition-all duration-300 transform translate-y-0 scale-100 animate-fadeIn ${
            toast.type === 'success' 
              ? 'border-emerald-200 bg-emerald-50/40' 
              : 'border-rose-200 bg-rose-50/40'
          }`}
        >
          {toast.type === 'success' ? (
            <CheckBadgeIcon className="w-6 h-6 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <ExclamationCircleIcon className="w-6 h-6 text-rose-600 shrink-0 mt-0.5" />
          )}
          <div className="flex-1">
            <h4 className={`text-xs font-black uppercase tracking-wider ${
              toast.type === 'success' ? 'text-emerald-800' : 'text-rose-800'
            }`}>
              {toast.type === 'success' ? 'Operación Exitosa' : 'Aviso del Sistema'}
            </h4>
            <p className="text-slate-600 text-[11px] mt-1 font-semibold leading-relaxed">
              {toast.message}
            </p>
          </div>
          <button 
            onClick={() => setToast(null)}
            className="text-slate-400 hover:text-slate-600 self-start text-xs font-bold px-1 rounded transition-colors"
          >
            ✕
          </button>
        </div>
      )}
    </ToastContext.Provider>
  );
}

// Custom Hook para devorar el contexto de forma limpia en cualquier pantalla
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast debe ser utilizado obligatoriamente dentro de un ToastProvider');
  }
  return context;
}