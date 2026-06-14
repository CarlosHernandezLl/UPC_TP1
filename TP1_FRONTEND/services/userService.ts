// src/services/userService.ts
import { User } from '../types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Función auxiliar para recuperar el token JWT desde la cookie de sesión
const getAuthToken = (): string => {
  if (typeof window === "undefined") return "";
  const value = `; ${document.cookie}`;
  const parts = value.split(`; scada_token=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || "";
  return "";
};

export interface AuditLog {
  id: number;
  action: string;
  user: string;
  timestamp: string;
  details: string;
}

export const userService = {
  // 1. Obtener todos los usuarios (Auditado y Protegido)
  async getUsers(): Promise<User[]> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users`, {
      cache: 'no-store',
      headers: {
        "Authorization": `Bearer ${token}` // ⬅️ ARREGLADO
      }
    });

    if (!res.ok) throw new Error('Error al obtener usuarios');
    return res.json();
  },

  // 2. Crear un usuario nuevo (Genera USER_CREATION en el Backend)
  async createUser(user: Omit<User, 'id'>): Promise<User> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${token}` // ⬅️ ARREGLADO
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al crear usuario');
    return res.json();
  },

  // 3. Eliminar / Revocar accesos de un usuario (Genera USER_REVOCATION en el Backend)
  async deleteUser(id: number): Promise<void> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${token}` // ⬅️ ARREGLADO
      }
    });

    if (!res.ok) throw new Error('Error al eliminar usuario');
  },

  // 4. Actualizar parámetros de un usuario (Genera USER_MODIFICATION en el Backend)
  async updateUser(id: number, user: Omit<User, 'id'>): Promise<User> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${token}` // ⬅️ ARREGLADO
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al actualizar usuario');
    return res.json();
  },

  // 5. Cargar el historial inmutable para la pestaña Audit Trail
  async getAuditLogs(): Promise<AuditLog[]> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/audit/`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!res.ok) throw new Error("Error cargando el Audit Trail");
    return await res.json();
  }
};