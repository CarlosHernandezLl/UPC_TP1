// src/services/userService.ts
import { User } from '../types/user';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export const userService = {
  // Obtener todos los usuarios
  async getUsers(): Promise<User[]> {
    const res = await fetch(`${API_URL}/users`, {
      cache: 'no-store',
    });
    
    if (!res.ok) throw new Error('Error al obtener usuarios');
    return res.json();
  },

  // Crear un usuario nuevo (¡Preparando el terreno para el POST!)
  async createUser(user: Omit<User, 'id'>): Promise<User> {
    const res = await fetch(`${API_URL}/users/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al crear usuario');
    return res.json();
  },

  // Eliminar un usuario
  async deleteUser(id: number): Promise<void> {
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'DELETE',
    });

    if (!res.ok) throw new Error('Error al eliminar usuario');
    // No necesitamos retornar el JSON si solo queremos confirmar la acción
  },
  
  async updateUser(id: number, user: Omit<User, 'id'>): Promise<User> {
    const res = await fetch(`${API_URL}/users/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(user),
    });

    if (!res.ok) throw new Error('Error al actualizar usuario');
    return res.json();
  },
  
};

