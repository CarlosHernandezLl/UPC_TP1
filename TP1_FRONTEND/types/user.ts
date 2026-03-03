// src/types/user.ts
export interface User {
    id: number;
    nombre: string;
    email: string;
    activo: boolean;
    password?: string; // Opcional, solo lo usaremos al crear
}