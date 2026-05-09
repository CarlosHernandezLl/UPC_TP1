import SideNav from "@/components/ui/SideNav";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    /* Cambiamos el contenedor principal a un blanco absoluto */
    <div className="flex h-screen flex-col md:flex-row md:overflow-hidden bg-white">
      {/* 1. BARRA LATERAL 
          Aseguramos que el fondo sea blanco o un gris ultra-claro (bg-slate-50) 
          y que el borde sea sutil.
      */}
      <div className="w-full flex-none md:w-64 bg-slate-50 border-r border-slate-100">
        <SideNav />
      </div>

      {/* 2. AREA DE CONTENIDO 
          Eliminamos cualquier rastro de bg-gray-950 y forzamos bg-white.
      */}
      <div className="flex-grow p-6 md:overflow-y-auto md:p-12 bg-white text-slate-900">
        {children}
      </div>
    </div>
  );
}
