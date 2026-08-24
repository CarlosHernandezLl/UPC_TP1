// src/services/userService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface User {
  id?: number;
  email: string;
  full_name: string;
  role: string;
  is_active?: boolean;
  password?: string;
}

export const userService = {
  async getUsers(): Promise<User[]> {
    const res = await fetch(`${API_URL}/users/`, {
      headers: { "Authorization": `Bearer ${getAuthToken()}` }
    });
    if (!res.ok) throw new Error('Error al obtener usuarios');
    return res.json();
  },

  async createUser(user: Omit<User, 'id'>): Promise<User> {
    const res = await fetch(`${API_URL}/users/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${getAuthToken()}` },
      body: JSON.stringify(user),
    });
    if (!res.ok) throw new Error('Error al crear usuario');
    return res.json();
  },

  async updateUser(id: number, user: Omit<User, 'id' | 'password'>): Promise<User> {
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', "Authorization": `Bearer ${getAuthToken()}` },
      body: JSON.stringify(user),
    });
    if (!res.ok) throw new Error('Error al actualizar usuario');
    return res.json();
  },

  async deleteUser(id: number): Promise<void> {
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'DELETE',
      headers: { "Authorization": `Bearer ${getAuthToken()}` }
    });
    if (!res.ok) throw new Error('Error al inhabilitar usuario');
  }
};