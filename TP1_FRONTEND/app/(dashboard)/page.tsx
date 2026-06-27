"use client";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center">
      <h1 className="text-5xl font-bold text-slate-900 mb-4">
        Bienvenido al Sistema de Soporte a la Decisión
      </h1>
      <p className="text-xl text-slate-500 max-w-2xl mb-12">
        Plataforma analítica y de optimización energética para sistemas HVAC en salas farmacéuticas. 
        Selecciona una opción en el menú lateral para comenzar la simulación.
      </p>

      {/* Resumen rápido / Cards informativas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
        <div className="p-6 bg-white rounded-xl border border-border shadow-sm text-left">
          <h3 className="font-semibold text-primary mb-2">Simulación y Análisis</h3>
          <p className="text-sm text-slate-600">
            Ingresa las variables de la sala para calcular la potencia mínima requerida bajo normativas GMP.
          </p>
        </div>
        <div className="p-6 bg-white rounded-xl border border-border shadow-sm text-left">
          <h3 className="font-semibold text-accent mb-2">Optimización Energética</h3>
          <p className="text-sm text-slate-600">
            El modelo predictivo está listo para proyectar escenarios y recomendar consignas de ahorro.
          </p>
        </div>
      </div>
    </div>
  );
}
