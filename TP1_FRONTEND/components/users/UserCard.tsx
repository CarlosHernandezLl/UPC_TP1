// src/components/users/UserCard.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { User } from '../../types/user';
import { userService } from '../../services/userService';

interface Props {
  user: User;
}

export default function UserCard({ user }: Props) {
  const router = useRouter();
  
  // 1. Estado para saber si estamos editando o viendo
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // 2. Estado temporal: Aquí guardamos lo que escribes ANTES de guardar
  // Lo iniciamos con los datos actuales del usuario
  const [editedUser, setEditedUser] = useState(user);

  // Función para guardar los cambios (PUT)
  const handleSave = async () => {
    try {
      // Llamamos al backend enviando el ID y los nuevos datos
      await userService.updateUser(user.id, editedUser);
      setIsEditing(false); // Salimos del modo edición
      router.refresh();    // Actualizamos la vista principal
    } catch (error) {
      alert("Error al actualizar");
    }
  };

  // Función para borrar (DELETE) - La que ya tenías
  const handleDelete = async () => {
    if (!confirm("¿Borrar usuario?")) return;
    setIsDeleting(true);
    await userService.deleteUser(user.id);
    router.refresh();
  };

  return (
    <div className="p-4 border rounded shadow-sm bg-gray-800 text-white flex flex-col gap-2">
      
      {/* ZONA DE DATOS (Usamos el operador ternario ? :) */}
      <div className="flex flex-col gap-2">
        
        {/* NOMBRE */}
        {isEditing ? (
          <input 
            className="p-1 rounded text-black"
            value={editedUser.nombre}
            onChange={(e) => setEditedUser({ ...editedUser, nombre: e.target.value })}
          />
        ) : (
          <h2 className="text-xl font-semibold">{user.nombre}</h2>
        )}

        {/* EMAIL */}
        {isEditing ? (
          <input 
            className="p-1 rounded text-black"
            value={editedUser.email}
            onChange={(e) => setEditedUser({ ...editedUser, email: e.target.value })}
          />
        ) : (
          <p className="text-gray-400">{user.email}</p>
        )}

        {/* ACTIVO/INACTIVO (Checkbox para editar) */}
        {isEditing ? (
          <label className="flex items-center gap-2">
            <input 
              type="checkbox"
              checked={editedUser.activo}
              onChange={(e) => setEditedUser({ ...editedUser, activo: e.target.checked })}
            />
            ¿Activo?
          </label>
        ) : (
          <span className={`text-sm ${user.activo ? "text-green-400" : "text-red-400"}`}>
            {user.activo ? "Activo" : "Inactivo"}
          </span>
        )}
      </div>

      {/* ZONA DE BOTONES */}
      <div className="flex gap-2 mt-2 justify-end">
        {isEditing ? (
          <>
            <button onClick={handleSave} className="bg-green-600 px-3 py-1 rounded">
              Guardar
            </button>
            <button onClick={() => setIsEditing(false)} className="bg-gray-600 px-3 py-1 rounded">
              Cancelar
            </button>
          </>
        ) : (
          <>
            <button onClick={() => setIsEditing(true)} className="bg-blue-600 px-3 py-1 rounded">
              Editar
            </button>
            <button 
              onClick={handleDelete} 
              disabled={isDeleting}
              className="bg-red-600 px-3 py-1 rounded"
            >
              {isDeleting ? "..." : "Eliminar"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}