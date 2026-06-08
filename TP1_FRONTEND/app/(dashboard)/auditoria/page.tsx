"use client";

import React, { useState, useEffect } from "react";
import { userService } from "@/services/userService";
import { User } from "@/types/user";
import {
  UserGroupIcon,
  UserPlusIcon,
  PencilSquareIcon,
  NoSymbolIcon,
  ClipboardDocumentCheckIcon,
  DocumentArrowDownIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

const mockupsAudit = [
  {
    id: 1,
    action: "Inicio de Sesión",
    user: "Carlos Pérez",
    timestamp: "2024-06-15 08:45:23",
    details: "Acceso exitoso desde IP 192.168.1.100",
  },
  {
    id: 2,
    action: "Creación de Usuario",
    user: "Carlos Pérez",
    timestamp: "2024-06-15 09:10:45",
    details: "Usuario 'jdoe' creado con rol SUPERVISOR",
  },
  {
    id: 3,
    action: "Edición de Usuario",
    user: "Carlos Pérez",
    timestamp: "2024-06-15 10:05:12",
    details: "Usuario'jdoe' actualizado: rol cambiado a GERENTE",
  },
  {
    id: 4,
    action: "Revocación de Usuario",
    user: "Carlos Pérez",
    timestamp: "2024-06-15 11:20:30",
    details: "Usuario 'jdoe' revocado permanentemente",
  },
  {
    id: 5,
    action: "Exportación de Reporte",
    user: "Carlos Pérez",
    timestamp: "2024-06-15 14:45:00",
    details: "Reporte de auditoría exportado en formato CSV",
  },
];

export default function AuditAndUsers() {
  const [activeTab, setActiveTab] = useState<"audit" | "users">("users");
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const [formData, setFormData] = useState({
    username: "",
    full_name: "",
    role: "SUPERVISOR",
    password: "",
  });

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await userService.getUsers();
      setUsers(data);
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === "users") loadUsers();
  }, [activeTab]);

  // Manejo de Modal
  const openCreateModal = () => {
    setEditingUser(null);
    setFormData({
      username: "",
      full_name: "",
      role: "SUPERVISOR",
      password: "",
    });
    setIsModalOpen(true);
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      full_name: user.full_name,
      role: user.role,
      password: "", // Contraseña vacía por seguridad en edición
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (editingUser) {
        // Lógica de actualización
        const updatePayload = { ...formData };
        if (!updatePayload.password) delete (updatePayload as any).password;
        await userService.updateUser(editingUser.id, updatePayload);
      } else {
        // Lógica de creación
        await userService.createUser(formData);
      }
      setIsModalOpen(false);
      loadUsers();
    } catch (error) {
      alert("Error en la operación técnica.");
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("¿Revocar acceso permanentemente?")) return;
    try {
      await userService.deleteUser(id);
      setUsers((prev) => prev.filter((u) => u.id !== id));
    } catch (err) {
      alert("Error al eliminar.");
    }
  };

  return (
    <div className="p-6 bg-white min-h-screen text-slate-900">
      <div className="max-w-7xl mx-auto">
        {/* Navegación de Pestañas */}
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Seguridad y Planta
            </h1>
            <p className="text-slate-500 text-sm italic">
              Gestión GxP de identidades autorizadas.
            </p>
          </div>
          <div className="flex bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-6 py-2 rounded-lg text-[10px] font-black uppercase ${activeTab === "audit" ? "bg-white text-primary shadow-sm" : "text-slate-400"}`}
            >
              Audit Trail
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`px-6 py-2 rounded-lg text-[10px] font-black uppercase ${activeTab === "users" ? "bg-white text-primary shadow-sm" : "text-slate-400"}`}
            >
              Usuarios
            </button>
          </div>
        </div>

        {activeTab === "audit" && (
          <div className="space-y-6 animate-fadeIn overflow-auto max-h-[70vh]">
            {mockupsAudit.map((entry) => (
              <div
                key={entry.id}
                className="bg-white border border-slate-100 rounded-2xl p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <h3 className="font-bold text-slate-900">{entry.action}</h3>
                  <span className="text-[10px] text-slate-400">
                    {entry.timestamp}
                  </span>
                </div>
                <p className="text-slate-600 mb-2">{entry.user}</p>
                <p className="text-[11px] text-slate-400 font-mono">
                  {entry.details}
                </p>
              </div>
            ))}
          </div>
        )}

        {activeTab === "users" && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Directorio de Personal</h2>
              <button
                onClick={openCreateModal}
                className="bg-primary text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 shadow-lg shadow-blue-100 flex items-center gap-2 transition-all"
              >
                <UserPlusIcon className="w-4 h-4" /> Nuevo Registro
              </button>
            </div>

            {loading ? (
              <div className="py-20 text-center animate-pulse text-slate-300 font-bold uppercase text-[10px]">
                Sincronizando...
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {users.map((user) => (
                  <div
                    key={user.id}
                    className="bg-white border border-slate-100 rounded-2xl p-6 hover:shadow-xl transition-all border-b-4 hover:border-b-primary"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="w-12 h-12 bg-slate-50 rounded-xl flex items-center justify-center text-primary font-black text-xl italic">
                        {user.full_name.charAt(0)}
                      </div>
                      <span
                        className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-tighter ${user.is_active ? "bg-emerald-50 text-emerald-600" : "bg-slate-100 text-slate-400"}`}
                      >
                        {user.role}
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-900">
                      {user.full_name}
                    </h3>
                    <p className="text-[11px] text-slate-400 mb-6 font-mono">
                      @{user.username}
                    </p>
                    <div className="flex gap-4 pt-4 border-t border-slate-50">
                      <button
                        onClick={() => openEditModal(user)}
                        className="flex-1 text-[10px] font-black text-slate-400 hover:text-primary uppercase flex items-center justify-center gap-1"
                      >
                        <PencilSquareIcon className="w-4 h-4" /> Editar
                      </button>
                      <button
                        onClick={() => handleDelete(user.id)}
                        className="flex-1 text-[10px] font-black text-slate-300 hover:text-rose-500 uppercase flex items-center justify-center gap-1"
                      >
                        <NoSymbolIcon className="w-4 h-4" /> Revocar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* MODAL UNIFICADO */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm">
            <div className="bg-white w-full max-w-md p-8 rounded-3xl shadow-2xl relative">
              <button
                onClick={() => setIsModalOpen(false)}
                className="absolute top-4 right-4 text-slate-300 hover:text-slate-600"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
              <h2 className="text-xl font-bold mb-6">
                {editingUser ? "Editar Usuario" : "Nuevo Registro"}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-[9px] font-black text-slate-400 uppercase mb-1">
                    Nombre Completo
                  </label>
                  <input
                    required
                    type="text"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                    value={formData.full_name}
                    onChange={(e) =>
                      setFormData({ ...formData, full_name: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-400 uppercase mb-1">
                    ID Usuario (Username)
                  </label>
                  <input
                    required
                    type="text"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                    value={formData.username}
                    onChange={(e) =>
                      setFormData({ ...formData, username: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-400 uppercase mb-1">
                    Rol
                  </label>
                  <select
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                    value={formData.role}
                    onChange={(e) =>
                      setFormData({ ...formData, role: e.target.value })
                    }
                  >
                    <option value="ADMIN">ADMIN</option>
                    <option value="SUPERVISOR">SUPERVISOR</option>
                    <option value="GERENTE">GERENTE</option>
                    <option value="AUDITOR">AUDITOR</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-400 uppercase mb-1">
                    {editingUser ? "Nueva Clave (Opcional)" : "Clave Temporal"}
                  </label>
                  <input
                    required={!editingUser}
                    type="password"
                    placeholder={editingUser ? "••••••••" : ""}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-primary"
                    value={formData.password}
                    onChange={(e) =>
                      setFormData({ ...formData, password: e.target.value })
                    }
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-primary text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-blue-700 shadow-lg shadow-blue-100 transition-all"
                >
                  {loading
                    ? "Procesando..."
                    : editingUser
                      ? "Guardar Cambios"
                      : "Crear Usuario"}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
