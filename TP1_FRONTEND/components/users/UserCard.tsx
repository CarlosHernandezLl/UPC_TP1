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
  
  // 1. Estado para control de flujo de renderizado dinámico
  const [isEditing, setIsEditing] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // 2. Estado temporal de mutación: Sincronizado con la interfaz estricta User
  const [editedUser, setEditedUser] = useState<User>(user);

  // Función para persistir cambios (PUT /users/{id})
  const handleSave = async () => {
    try {
      // Enviamos el objeto con el tipado exacto exigido por el endpoint
      await userService.updateUser(user.id, editedUser);
      setIsEditing(false); // Retorno a vista de lectura
      router.refresh();    // Mutación de estado en el Server Component principal
    } catch (error) {
      alert("Error al actualizar la identidad en el servidor.");
    }
  };

  // Función para revocar credenciales (DELETE /users/{id})
  const handleDelete = async () => {
    if (!confirm("¿Revocar acceso permanentemente a este operador?")) return;
    try {
      setIsDeleting(true);
      await userService.deleteUser(user.id);
      router.refresh();
    } catch (error) {
      alert("Error al intentar eliminar el registro.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="p-4 border border-slate-700 rounded-2xl shadow-sm bg-gray-800 text-white flex flex-col gap-2">
      
      {/* ZONA DE CONTROL DE DATOS GxP */}
      <div className="flex flex-col gap-2">
        
        {/* FILA: NOMBRE COMPLETO */}
        {isEditing ? (
          <input 
            className="p-2 rounded-xl text-black font-medium text-sm outline-none"
            value={editedUser.full_name}
            onChange={(e) => setEditedUser({ ...editedUser, full_name: e.target.value })}
          />
        ) : (
          <h2 className="text-lg font-bold tracking-tight text-slate-100">{user.full_name}</h2>
        )}

        {/* FILA: IDENTIFICADOR / USERNAME (Corregido de email a username) */}
        {isEditing ? (
          <input 
            className="p-2 rounded-xl text-black font-mono text-xs outline-none"
            value={editedUser.username}
            onChange={(e) => setEditedUser({ ...editedUser, username: e.target.value })}
          />
        ) : (
          <p className="text-xs font-mono text-slate-400">@{user.username}</p>
        )}

        {/* FILA: ESTADO OPERATIVO (Corregido de activo a is_active) */}
        {isEditing ? (
          <label className="flex items-center gap-2 text-xs font-black uppercase tracking-wider text-slate-300 select-none cursor-pointer">
            <input 
              type="checkbox"
              className="w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
              checked={editedUser.is_active}
              onChange={(e) => setEditedUser({ ...editedUser, is_active: e.target.checked })}
            />
            Acceso Habilitado
          </label>
        ) : (
          <span className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full w-max ${user.is_active ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
            {user.is_active ? "Activo" : "Inactivo"}
          </span>
        )}
      </div>

      {/* COMPONENTE INTERACTIVO DE ACCIONES */}
      <div className="flex gap-2 mt-4 justify-end border-t border-slate-700/50 pt-3">
        {isEditing ? (
          <>
            <button onClick={handleSave} className="bg-emerald-600 hover:bg-emerald-700 px-4 py-1.5 rounded-lg text-xs font-bold transition-colors">
              Guardar
            </button>
            <button onClick={() => { setEditedUser(user); setIsEditing(false); }} className="bg-slate-600 hover:bg-slate-700 px-4 py-1.5 rounded-lg text-xs font-bold transition-colors">
              Cancelar
            </button>
          </>
        ) : (
          <>
            <button onClick={() => setIsEditing(true)} className="bg-blue-600 hover:bg-blue-700 px-4 py-1.5 rounded-lg text-xs font-bold transition-colors">
              Editar
            </button>
            <button 
              onClick={handleDelete} 
              disabled={isDeleting}
              className="bg-rose-600 hover:bg-rose-700 px-4 py-1.5 rounded-lg text-xs font-bold transition-colors disabled:bg-slate-700 disabled:text-slate-500"
            >
              {isDeleting ? "..." : "Eliminar"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}