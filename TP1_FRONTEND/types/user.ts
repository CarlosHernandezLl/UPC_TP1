// src/types/user.ts
// export interface User {
//     id: number;
//     nombre: string;
//     email: string;
//     activo: boolean;
//     password?: string; // Opcional, solo lo usaremos al crear
// }

export interface User {
  id: number;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
}