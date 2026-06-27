// src/services/userService.ts
import { User } from '../types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

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
  async getUsers(): Promise<User[]> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users`, {
      cache: 'no-store',
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!res.ok) throw new Error('Error al obtener usuarios');
    return res.json();
  },

  async createUser(user: Omit<User, 'id'>): Promise<User> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al crear usuario');
    return res.json();
  },

  async deleteUser(id: number): Promise<void> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'DELETE',
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!res.ok) throw new Error('Error al eliminar usuario');
  },

  async updateUser(id: number, user: Omit<User, 'id'>): Promise<User> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al actualizar usuario');
    return res.json();
  },

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
  },

  async exportAppliedRecommendationsCSV(): Promise<Blob> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/audit/export-applied-csv`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}` // Enlace seguro obligatorio
      }
    });

    if (!res.ok) throw new Error("No se pudo descargar el reporte de auditoría");

    return await res.blob();
  }
};