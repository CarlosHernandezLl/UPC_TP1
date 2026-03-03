// src/components/users/UserForm.tsx
"use client"; // 👈 Esto le dice a Next.js que este componente vive en el navegador

import { useState } from "react";
import { userService } from "@/services/userService";
import { useRouter } from "next/navigation"; // Para recargar la página

export default function UserForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    nombre: "",
    email: "",
    password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      // 1. Llamamos a nuestro servicio
      await userService.createUser({
        ...formData,
        activo: true, // Por defecto lo creamos activo
      });

      // 2. Limpiamos el formulario
      setFormData({ nombre: "", email: "", password: "" });
      
      // 3. Recargamos la página para ver el nuevo usuario en la lista
      router.refresh();
      
    } catch (error) {
      alert("Error al crear usuario");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mb-8 p-4 bg-gray-900 rounded border border-gray-700 w-full max-w-md">
      <h2 className="text-xl font-bold mb-4 text-white">Nuevo Usuario</h2>
      
      <div className="flex flex-col gap-3">
        <input
          type="text"
          placeholder="Nombre"
          className="p-2 rounded bg-gray-800 text-white border border-gray-600"
          value={formData.nombre}
          onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
          required
        />
        <input
          type="email"
          placeholder="Email"
          className="p-2 rounded bg-gray-800 text-white border border-gray-600"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
        />
        <input
          type="password"
          placeholder="Password"
          className="p-2 rounded bg-gray-800 text-white border border-gray-600"
          value={formData.password}
          onChange={(e) => setFormData({ ...formData, password: e.target.value })}
          required
        />
        
        <button 
          type="submit" 
          className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-2 px-4 rounded mt-2 transition-colors"
        >
          Guardar Usuario
        </button>
      </div>
    </form>
  );
}