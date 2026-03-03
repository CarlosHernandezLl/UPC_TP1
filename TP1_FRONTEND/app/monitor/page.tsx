// src/app/monitor/page.tsx
import PLCControl from "@/components/plc/PLCControl";
import PLCTrend from "@/components/plc/PLCTrend"; // 👈 1. Importas el nuevo componente

export default function MonitorPage() {
  return (
    <div className="flex flex-col items-center w-full min-h-screen bg-gray-950 p-6">
      <h1 className="text-3xl font-bold mb-8 text-blue-400">
        Panel de Control SCADA
      </h1>

      {/* Contenedor principal para organizar los elementos */}
      <div className="w-full max-w-6xl flex flex-col gap-8 items-center">
        
        {/* Aquí está tu control actual del PLC */}
        <PLCControl />

        {/* 👇 2. AQUÍ AGREGAS LA GRÁFICA DE TENDENCIAS 👇 */}
        <PLCTrend />
        
      </div>
    </div>
  );
}