"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { authService } from '@/services/authService';
import {
  CpuChipIcon,
  CircleStackIcon,
  BeakerIcon,
  ShieldCheckIcon,
  ArrowLeftOnRectangleIcon,
  UserCircleIcon,
  HomeIcon,
} from '@heroicons/react/24/outline';

const links = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Ingesta de Datos', href: '/ingesta', icon: CircleStackIcon },
  { name: 'Entrenamiento IA', href: '/ia-control', icon: CpuChipIcon },
  { name: 'Simulador de Ahorro', href: '/simulador', icon: BeakerIcon },
  { name: 'Auditoria', href: '/auditoria', icon: ShieldCheckIcon },
];

export default function SideNav() {
  const pathname = usePathname();
  const [userName, setUserName] = useState("Cargando...");
  const [userEmail, setUserEmail] = useState("");
  const [userRole, setUserRole] = useState("a");

  useEffect(() => {
    // Recuperamos los datos del operador guardados en el Login
    const storedName = localStorage.getItem("scada_userName");
    const storedEmail = localStorage.getItem("scada_userEmail");
    const storedRole = localStorage.getItem("scada_userRole");

    setUserName(storedName || "Operador");
    if (storedEmail) setUserEmail(storedEmail);
    if (storedRole) setUserRole(storedRole);
  }, [pathname]);

  // Si estás en el Login, no renderizamos la barra de navegación lateral
  if (pathname === '/login') return null;

  // Filtrado dinámico de pestañas para cumplimiento normativo GxP
  const visibleLinks = links.filter((link) => {
    return true;
  });

  return (
    <div className="flex h-full flex-col px-3 py-4 md:px-2 bg-white border-r border-slate-200 shadow-sm">

      {/* Header del Menú - Azul Farmacéutico */}
      <div className="mb-4 flex h-20 items-center justify-start rounded-xl bg-blue-600 p-4 md:h-28 shadow-md shadow-blue-100">
        <div className="text-white">
          <h1 className="text-lg font-bold leading-tight tracking-tight">Energy Reduction</h1>
          <p className="text-[10px] uppercase tracking-widest opacity-90 font-black">Planta Farmacéutica</p>
        </div>
      </div>

      <div className="flex grow flex-row justify-between space-x-2 md:flex-col md:space-x-0 md:space-y-1.5">
        {visibleLinks.map((link) => {
          const LinkIcon = link.icon;
          const isActive = pathname === link.href;

          return (
            <Link
              key={link.name}
              href={link.href}
              className={`flex h-12 grow items-center justify-center gap-3 rounded-xl p-3 text-sm font-bold transition-all md:flex-none md:justify-start md:px-4
              ${isActive
                  ? 'bg-blue-50 text-blue-600 border-l-4 border-blue-600'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-blue-600 border-l-4 border-transparent'
                }
              `}
            >
              <LinkIcon className={`w-5 h-5 ${isActive ? 'text-blue-600' : 'text-slate-400'}`} />
              <p className="hidden md:block text-xs uppercase tracking-tight">{link.name}</p>
            </Link>
          );
        })}

        <div className="hidden h-auto w-full grow md:block"></div>

        {/* ZONA DE USUARIO Y CIERRE DE SESIÓN */}
        <div className="flex flex-col gap-1 mt-4 pt-4 border-t border-slate-100">

          {/* Perfil de Usuario Conectado */}
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-slate-50 border border-slate-100 mb-2">
            <UserCircleIcon className="w-9 h-9 text-slate-400 shrink-0" />
            <div className="hidden md:block overflow-hidden">
              <p className="text-xs font-black text-slate-700 truncate">{userName}</p>
              <div className="mt-0.5">
                <span className={`inline-block text-[8px] font-extrabold px-1.5 py-0.5 rounded uppercase tracking-wider border ${userRole === 'ADMIN'
                    ? 'bg-indigo-50 text-indigo-600 border-indigo-100'
                    : userRole === 'SUPERVISOR'
                      ? 'bg-blue-50 text-blue-600 border-blue-100'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}>
                  {userRole}
                </span>
              </div>
            </div>
          </div>

          {/* Botón de Cerrar Sesión */}
          <button
            onClick={() => authService.logout()}
            className="flex h-11 items-center justify-center gap-3 rounded-xl px-4 text-xs font-black uppercase tracking-wider text-rose-500 hover:bg-rose-50 transition-colors md:justify-start group"
          >
            <ArrowLeftOnRectangleIcon className="w-5 h-5 transition-transform group-hover:-translate-x-1 text-rose-400" />
            <span className="hidden md:block">Finalizar Sesión</span>
          </button>
        </div>

      </div>
    </div>
  );
}