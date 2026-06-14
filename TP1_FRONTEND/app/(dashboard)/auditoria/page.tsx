"use client";

import React, { useState, useEffect } from "react";
import { userService, AuditLog } from "@/services/userService"; // Importa la nueva interfaz AuditLog
import { User } from "@/types/user";
import {
  UserPlusIcon,
  PencilSquareIcon,
  NoSymbolIcon,
  XMarkIcon,
  ArrowPathRoundedSquareIcon
} from "@heroicons/react/24/outline";

export default function AuditAndUsers() {
  const [activeTab, setActiveTab] = useState<"audit" | "users">("users");

  // Estados para Usuarios
  const [users, setUsers] = useState<User[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Estados para Audit Trail (¡Nueva data real!)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loadingAudit, setLoadingAudit] = useState(false);

  // Estados del Modal
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
      setLoadingUsers(true);
      const data = await userService.getUsers();
      setUsers(data);
    } catch (error) {
      console.error("Error cargando usuarios:", error);
    } finally {
      setLoadingUsers(false);
    }
  };

  const loadAuditLogs = async () => {
    try {
      setLoadingAudit(true);
      const data = await userService.getAuditLogs();
      setAuditLogs(data);
    } catch (error) {
      console.error("Error cargando Audit Trail:", error);
    } finally {
      setLoadingAudit(false);
    }
  };

  // El useEffect ahora reacciona a qué pestaña está activa
  useEffect(() => {
    if (activeTab === "users") loadUsers();
    if (activeTab === "audit") loadAuditLogs();
  }, [activeTab]);

  // Manejo de Modal
  const openCreateModal = () => {
    setEditingUser(null);
    setFormData({ username: "", full_name: "", role: "SUPERVISOR", password: "" });
    setIsModalOpen(true);
  };

  const openEditModal = (user: User) => {
    setEditingUser(user);
    setFormData({
      username: user.username,
      full_name: user.full_name,
      role: user.role,
      password: "",
    });
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingUsers(true);
    try {
      if (editingUser) {
        const updatePayload = { ...formData };
        if (!updatePayload.password) delete (updatePayload as any).password;
        await userService.updateUser(editingUser.id, updatePayload);
      } else {
        await userService.createUser(formData);
      }
      setIsModalOpen(false);
      loadUsers();
    } catch (error) {
      alert("Error en la operación técnica.");
    } finally {
      setLoadingUsers(false);
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
    <div className="p-6 bg-gray-50 min-h-screen text-slate-900">
      <div className="max-w-7xl mx-auto">

        {/* Navegación de Pestañas */}
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Seguridad y Planta</h1>
            <p className="text-slate-500 text-sm italic">Gestión GxP de identidades autorizadas y registros.</p>
          </div>
          <div className="flex bg-slate-200/50 p-1 rounded-xl border border-slate-200 shadow-inner">
            <button
              onClick={() => setActiveTab("audit")}
              className={`px-6 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${activeTab === "audit" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Audit Trail
            </button>
            <button
              onClick={() => setActiveTab("users")}
              className={`px-6 py-2 rounded-lg text-[10px] font-black uppercase transition-all ${activeTab === "users" ? "bg-white text-blue-600 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
            >
              Usuarios
            </button>
          </div>
        </div>

        {/* PESTAÑA: AUDIT TRAIL */}
        {activeTab === "audit" && (
          <div className="space-y-6 overflow-auto max-h-[75vh] pr-2">
            <h2 className="text-xl font-bold mb-4">Registro Histórico Inmutable (21 CFR Part 11)</h2>

            {loadingAudit ? (
              <div className="py-20 flex flex-col items-center justify-center text-slate-400">
                <ArrowPathRoundedSquareIcon className="w-8 h-8 animate-spin mb-2" />
                <span className="text-[10px] font-bold uppercase">Cargando Trazabilidad...</span>
              </div>
            ) : auditLogs.length === 0 ? (
              <div className="py-20 text-center text-slate-400 text-sm">No hay registros de auditoría disponibles.</div>
            ) : (
              auditLogs.map((entry) => (
                <div key={entry.id} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm border-l-4 border-l-slate-400 hover:border-l-blue-500 transition-colors">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-bold text-slate-800 tracking-tight">{entry.action}</h3>
                    <span className="text-[10px] font-black bg-slate-100 text-slate-500 px-3 py-1 rounded-full uppercase">
                      {entry.timestamp}
                    </span>
                  </div>
                  <p className="text-sm font-bold text-blue-600 mb-1 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    {entry.user}
                  </p>
                  <p className="text-xs text-slate-500 font-mono bg-slate-50 p-3 rounded-lg border border-slate-100">
                    {entry.details}
                  </p>
                </div>
              ))
            )}
          </div>
        )}

        {/* PESTAÑA: USUARIOS */}
        {activeTab === "users" && (
          <div className="space-y-6 animate-fadeIn">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-bold">Directorio de Personal</h2>
              <button
                onClick={openCreateModal}
                className="bg-slate-900 text-white px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-800 shadow-md flex items-center gap-2 transition-all"
              >
                <UserPlusIcon className="w-4 h-4" /> Nuevo Registro
              </button>
            </div>

            {loadingUsers ? (
              <div className="py-20 flex flex-col items-center justify-center text-slate-400">
                <ArrowPathRoundedSquareIcon className="w-8 h-8 animate-spin mb-2" />
                <span className="text-[10px] font-bold uppercase">Sincronizando Usuarios...</span>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {users.map((user) => (
                  <div key={user.id} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all border-b-4 hover:border-b-blue-500">
                    <div className="flex justify-between items-start mb-4">
                      <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center text-blue-600 font-black text-xl italic border border-blue-100">
                        {user.full_name.charAt(0)}
                      </div>
                      <span className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-tighter ${user.is_active ? "bg-emerald-50 text-emerald-600 border border-emerald-100" : "bg-slate-100 text-slate-400"}`}>
                        {user.role}
                      </span>
                    </div>
                    <h3 className="font-bold text-slate-900">{user.full_name}</h3>
                    <p className="text-[11px] text-slate-400 mb-6 font-mono">@{user.username}</p>
                    <div className="flex gap-4 pt-4 border-t border-slate-100">
                      <button onClick={() => openEditModal(user)} className="flex-1 text-[10px] font-black text-slate-400 hover:text-blue-600 uppercase flex items-center justify-center gap-1 transition-colors">
                        <PencilSquareIcon className="w-4 h-4" /> Editar
                      </button>
                      <button onClick={() => handleDelete(user.id)} className="flex-1 text-[10px] font-black text-slate-300 hover:text-rose-500 uppercase flex items-center justify-center gap-1 transition-colors">
                        <NoSymbolIcon className="w-4 h-4" /> Revocar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* MODAL UNIFICADO (Se mantiene igual) */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
            <div className="bg-white w-full max-w-md p-8 rounded-3xl shadow-2xl relative animate-fadeIn">
              <button onClick={() => setIsModalOpen(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-800 transition-colors">
                <XMarkIcon className="w-6 h-6" />
              </button>
              <h2 className="text-xl font-bold mb-6 text-slate-800">
                {editingUser ? "Editar Usuario" : "Nuevo Registro"}
              </h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-[9px] font-black text-slate-500 uppercase mb-1 tracking-wider">Nombre Completo</label>
                  <input required type="text" className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium" value={formData.full_name} onChange={(e) => setFormData({ ...formData, full_name: e.target.value })} />
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-500 uppercase mb-1 tracking-wider">ID Usuario (Username)</label>
                  <input required type="text" className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium" value={formData.username} onChange={(e) => setFormData({ ...formData, username: e.target.value })} />
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-500 uppercase mb-1 tracking-wider">Rol de Acceso</label>
                  <select className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium font-bold text-slate-700" value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })}>
                    <option value="ADMIN">ADMIN (Acceso Total)</option>
                    <option value="SUPERVISOR">SUPERVISOR (Aplica Recomendaciones)</option>
                    <option value="GERENTE">GERENTE (Visualiza ROI)</option>
                    <option value="AUDITOR">AUDITOR (Solo Lectura GMP)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[9px] font-black text-slate-500 uppercase mb-1 tracking-wider">
                    {editingUser ? "Nueva Clave (Opcional)" : "Clave Temporal"}
                  </label>
                  <input required={!editingUser} type="password" placeholder={editingUser ? "••••••••" : "Ingrese clave"} className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:ring-2 focus:ring-blue-500 font-medium" value={formData.password} onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
                </div>
                <button type="submit" disabled={loadingUsers} className="w-full py-4 mt-2 bg-blue-600 text-white rounded-xl text-[11px] font-black uppercase tracking-widest hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all disabled:bg-slate-300">
                  {loadingUsers ? "Procesando Transacción..." : editingUser ? "Guardar Cambios" : "Crear Identidad GxP"}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}