// src/components/users/UserForm.tsx
"use client"; 

import { useState } from "react";
import { userService } from "@/services/userService";
import { useRouter } from "next/navigation"; 

export default function UserForm() {
  const router = useRouter();
  
  // 1. Sincronizamos el estado con la nomenclatura oficial en inglés ( types/user.ts)
  const [formData, setFormData] = useState({
    username: "",
    full_name: "",
    role: "SUPERVISOR", // Rol base por defecto para el personal de planta
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 2. Construimos el payload real respetando el contrato Omit<User, "id"> e is_active
      await userService.createUser({
        username: formData.username,
        full_name: formData.full_name,
        role: formData.role,
        is_active: true, // Corregido: de 'activo' a 'is_active'
        password: formData.password, // Se inyecta la clave para el hash de FastAPI
      } as any); // Usamos cast de escape por si la interfaz base Omit estricta no declara la propiedad de password

      // 3. Limpiamos el formulario con las propiedades correctas
      setFormData({ username: "", full_name: "", role: "SUPERVISOR", password: "" });
      
      // 4. Forzamos el refresco para actualizar instantáneamente las grillas del Dashboard/Auditoría
      router.refresh();
      alert("Identidad autorizada creada con éxito.");
      
    } catch (error) {
      console.error("Error al registrar operador:", error);
      alert("Error técnico al crear la credencial GxP.");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-8 p-6 bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-md shadow-lg">
      <h2 className="text-xl font-bold mb-4 text-white tracking-tight">Nuevo Registro de Personal</h2>
      
      <div className="flex flex-col gap-4">
        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase mb-1 tracking-wider">Nombre Completo</label>
          <input
            type="text"
            placeholder="Ej. Carlos Hernandez"
            className="w-full p-2.5 rounded-xl bg-gray-800 text-white border border-gray-600 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase mb-1 tracking-wider">ID Usuario (Username)</label>
          <input
            type="text"
            placeholder="Ej. chernandez"
            className="w-full p-2.5 rounded-xl bg-gray-800 text-white border border-gray-600 text-sm font-mono outline-none focus:ring-2 focus:ring-blue-500"
            value={formData.username}
            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
            required
          />
        </div>

        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase mb-1 tracking-wider">Rol en Planta</label>
          <select 
            className="w-full p-2.5 rounded-xl bg-gray-800 text-white border border-gray-600 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-bold"
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          >
            <option value="SUPERVISOR">SUPERVISOR (Aplica Recomendación)</option>
            <option value="ADMIN">ADMINISTRADOR (Control de MLOps)</option>
            <option value="AUDITOR">AUDITOR (Solo Lectura GxP)</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] font-black text-slate-400 uppercase mb-1 tracking-wider">Clave Temporal</label>
          <input
            type="password"
            placeholder="••••••••"
            className="w-full p-2.5 rounded-xl bg-gray-800 text-white border border-gray-600 text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            required
          />
        </div>
        
        <button 
          type="submit" 
          className="bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-widest py-3 px-4 rounded-xl mt-2 transition-all shadow-md shadow-blue-900/20"
        >
          Guardar e Inmuta Registro
        </button>
      </div>
    </form>
  );
}