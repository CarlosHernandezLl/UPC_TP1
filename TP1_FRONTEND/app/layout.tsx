import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import SideNav from "@/components/ui/SideNav"; // ✅ Importamos el menú

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sistema SCADA",
  description: "Monitor y Control de Planta",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-gray-950 text-gray-100`}
      >
        {/* --- ESTRUCTURA PRINCIPAL (LAYOUT) --- */}
        {/* Usamos h-screen para ocupar toda la altura de la ventana */}
        <div className="flex h-screen flex-col md:flex-row md:overflow-hidden">
          
          {/* 1. BARRA LATERAL (Izquierda) */}
          {/* En móvil ocupa todo el ancho, en PC se fija a 64 unidades de ancho */}
          <div className="w-full flex-none md:w-64">
            <SideNav />
          </div>

          {/* 2. AREA DE CONTENIDO (Derecha) */}
          {/* flex-grow hace que ocupe todo el espacio sobrante */}
          {/* overflow-y-auto permite hacer scroll solo en el contenido, no en el menú */}
          <div className="flex-grow p-6 md:overflow-y-auto md:p-12 bg-gray-950">
            {children}
          </div>

        </div>
      </body>
    </html>
  );
}