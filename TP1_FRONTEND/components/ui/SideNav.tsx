"use client"; // Necesario porque usaremos estado y localStorage

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { authService } from '@/services/authService'; // 👈 Importamos el servicio
import {
  CpuChipIcon,
  UserGroupIcon,
  HomeIcon,
  ChartBarIcon,
  ArrowLeftOnRectangleIcon, // Icono para salir
  UserCircleIcon            // Icono para el usuario
} from '@heroicons/react/24/outline';

const links = [
  { name: 'Inicio', href: '/', icon: HomeIcon },
  { name: 'Monitor PLC', href: '/monitor', icon: CpuChipIcon },
  { name: 'Usuarios', href: '/usuarios', icon: UserGroupIcon },
  { name: 'Historial', href: '/historial', icon: ChartBarIcon },
];

export default function SideNav() {
  const pathname = usePathname();
  // Estado para guardar el nombre del usuario
  const [userName, setUserName] = useState("Cargando...");
  const [userEmail, setUserEmail] = useState("");

  // Al cargar el menú, leemos el nombre guardado en localStorage
  useEffect(() => {
    const storedName = localStorage.getItem("scada_userName");
    const storedEmail = localStorage.getItem("scada_userEmail");
    if (storedName) {
      setUserName(storedName);
    } else {
      setUserName("Operador"); // Valor por defecto si no se encuentra
    }
    if (storedEmail) {
      setUserEmail(storedEmail);
    }
    
  }, [pathname]);

  if (pathname === '/login') {
    return null; 
  }

  const visibleLinks = links.filter((link) => {
    if (link.name === 'Usuarios' && userEmail !== 'administrador@acfarma.com') {
      return false; // Lo ocultamos
    }
    return true; // Mostramos los demás
  });
  
  return (
    <div className="flex h-full flex-col px-3 py-4 md:px-2 bg-gray-950 border-r border-gray-800">
      
      <div className="mb-2 flex h-20 items-end justify-start rounded-md bg-blue-950 p-4 md:h-32">
        <div className="text-white w-32 md:w-40">
           <h1 className="text-xl font-bold">SCADA v1.0</h1>
           <p className="text-xs opacity-80">Planta Principal</p>
        </div>
      </div>

      <div className="flex grow flex-row justify-between space-x-2 md:flex-col md:space-x-0 md:space-y-2">
        {visibleLinks.map((link) => {
          const LinkIcon = link.icon;
          return (
            <Link
              key={link.name}
              href={link.href}
              className={`flex h-[48px] grow items-center justify-center gap-2 rounded-md p-3 text-sm font-medium hover:bg-gray-800 hover:text-blue-400 md:flex-none md:justify-start md:p-2 md:px-3
              ${pathname === link.href 
                 ? 'bg-gray-800 text-blue-400 border border-gray-700' 
                 : 'text-gray-400 border border-transparent'
              }
              `}
            >
              <LinkIcon className="w-6" />
              <p className="hidden md:block">{link.name}</p>
            </Link>
          );
        })}
        
        <div className="hidden h-auto w-full grow rounded-md md:block"></div>
        
        {/* 👇 ZONA DE USUARIO Y CIERRE DE SESIÓN 👇 */}
        <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-gray-800">
          
          {/* Tarjeta con el Nombre del Usuario */}
          <div className="flex items-center gap-3 px-3 py-2 text-gray-300">
            <UserCircleIcon className="w-8 h-8 text-blue-400" />
            <div className="hidden md:block overflow-hidden">
              <p className="text-sm font-semibold truncate">{userName}</p>
              <p className="text-xs text-green-500">En línea</p>
            </div>
          </div>

          {/* Botón de Cerrar Sesión */}
          <button 
            onClick={() => authService.logout()}
            className="flex h-[48px] items-center justify-center gap-2 rounded-md p-3 text-sm font-medium text-red-400 hover:bg-red-950/30 hover:text-red-300 md:justify-start transition-colors"
          >
            <ArrowLeftOnRectangleIcon className="w-6" />
            <span className="hidden md:block">Cerrar Sesión</span>
          </button>
        </div>

      </div>
    </div>
  );
}