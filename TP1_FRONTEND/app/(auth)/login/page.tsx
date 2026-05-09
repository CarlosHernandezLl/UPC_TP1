"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authService } from "@/services/authService";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await authService.login(username, password);

      // Configuración de Cookies (Accesibles por Middleware)
      const cookieConfig = "path=/; max-age=86400; SameSite=Lax";
      document.cookie = `scada_token=${data.access_token}; ${cookieConfig}`;
      document.cookie = `scada_email=${username}; ${cookieConfig}`;

      // Persistencia local para la UI
      localStorage.setItem("scada_userName", data.user_info.full_name);
      localStorage.setItem("scada_userEmail", username);

      router.push("/");
      router.refresh();
    } catch (err: any) {
      setError(err.message || "Error al iniciar sesión");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-50">
      <div className="w-full max-w-md p-8 bg-white border border-slate-200 rounded-xl shadow-lg">
        {/* Encabezado */}
        <div className="mb-8 text-center">
          <h2 className="text-2xl font-bold text-slate-800">HVAC Simulator</h2>
          <p className="text-sm text-slate-500 mt-1">
            Gestión de Eficiencia Energética
          </p>
        </div>

        {/* Mensaje de Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-lg mb-6 text-center text-sm font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <div>
            <label className="block text-slate-700 text-sm font-semibold mb-1.5">
              Usuario
            </label>
            <input
              type="text"
              placeholder="Ej. chernandez"
              className="w-full px-4 py-2.5 rounded-lg bg-white text-slate-900 border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all placeholder:text-slate-400"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div>
            <label className="block text-slate-700 text-sm font-semibold mb-1.5">
              Contraseña
            </label>
            <input
              type="password"
              placeholder="••••••••"
              className="w-full px-4 py-2.5 rounded-lg bg-white text-slate-900 border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className={`w-full mt-2 py-2.5 px-4 rounded-lg font-bold text-white transition-all
              ${
                loading
                  ? "bg-blue-400 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700 active:transform active:scale-[0.98] shadow-md shadow-blue-200"
              }`}
          >
            {loading ? "Autenticando..." : "Ingresar al Sistema"}
          </button>
        </form>

        {/* Footer opcional */}
        <p className="mt-8 text-center text-xs text-slate-400 uppercase tracking-widest font-medium">
          Control de Procesos Industrial
        </p>
      </div>
    </div>
  );
}
