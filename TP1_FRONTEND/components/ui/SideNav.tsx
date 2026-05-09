"use client";

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { authService } from '@/services/authService';
import {
  CpuChipIcon,
  CircleStackIcon,
  BeakerIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ArrowLeftOnRectangleIcon,
  UserCircleIcon,
  LayoutDashboardIcon, // Si no tienes este, usa HomeIcon
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
  // const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const storedName = localStorage.getItem("scada_userName");
    const storedEmail = localStorage.getItem("scada_userEmail");
    setUserName(storedName || "Operador");
    // if (storedEmail) setUserEmail(storedEmail);
  }, [pathname]);

  if (pathname === '/login') return null;

  const visibleLinks = links.filter((link) => {
    if (link.name === 'Usuarios' && userEmail !== 'administrador@acfarma.com') {
      return false;
    }
    return true;
  });
  
  return (
    <div className="flex h-full flex-col px-3 py-4 md:px-2 bg-card border-r border-border shadow-sm">
      
      {/* Header del Menú - Azul Médico */}
      <div className="mb-4 flex h-20 items-center justify-start rounded-xl bg-primary p-4 md:h-28 shadow-md shadow-blue-100">
        <div className="text-white">
           <h1 className="text-lg font-bold leading-tight">Energy Reduction</h1>
           <p className="text-[10px] uppercase tracking-wider opacity-90 font-medium">Planta Farmacéutica</p>
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
              className={`flex h-[48px] grow items-center justify-center gap-3 rounded-lg p-3 text-sm font-semibold transition-all md:flex-none md:justify-start md:px-4
              ${isActive 
                  ? 'bg-blue-50 text-primary border-l-4 border-primary' 
                  : 'text-slate-500 hover:bg-slate-50 hover:text-primary border-l-4 border-transparent'
              }
              `}
            >
              <LinkIcon className={`w-5 h-5 ${isActive ? 'text-primary' : 'text-slate-400'}`} />
              <p className="hidden md:block">{link.name}</p>
            </Link>
          );
        })}
        
        <div className="hidden h-auto w-full grow md:block"></div>
        
        {/* ZONA DE USUARIO Y CIERRE DE SESIÓN */}
        <div className="flex flex-col gap-1 mt-4 pt-4 border-t border-border">
          
          {/* Perfil de Usuario */}
          <div className="flex items-center gap-3 px-3 py-3 rounded-lg bg-slate-50/50 border border-slate-100 mb-2">
            <UserCircleIcon className="w-9 h-9 text-slate-400" />
            <div className="hidden md:block overflow-hidden">
              <p className="text-xs font-bold text-slate-700 truncate">{userName}</p>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
                <p className="text-[10px] font-medium text-slate-500 uppercase">Sistema Activo</p>
              </div>
            </div>
          </div>

          {/* Botón de Cerrar Sesión */}
          <button 
            onClick={() => authService.logout()}
            className="flex h-[44px] items-center justify-center gap-3 rounded-lg px-4 text-sm font-bold text-red-500 hover:bg-red-50 transition-colors md:justify-start group"
          >
            <ArrowLeftOnRectangleIcon className="w-5 h-5 transition-transform group-hover:-translate-x-1" />
            <span className="hidden md:block">Finalizar Sesión</span>
          </button>
        </div>

      </div>
    </div>
  );
}