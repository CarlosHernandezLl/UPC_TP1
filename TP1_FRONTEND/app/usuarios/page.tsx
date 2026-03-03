// src/app/usuarios/page.tsx
import { userService } from "@/services/userService";
import UserForm from "@/components/users/UserForm";
import UserCard from "@/components/users/UserCard";

// Herramientas de Next.js para leer cookies y redirigir desde el servidor
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function UsuariosPage() {
  // --- 1. CAPA DE SEGURIDAD (Se ejecuta en el servidor) ---
  // Obtenemos las cookies. En las versiones recientes de Next.js, cookies() requiere 'await'
  const cookieStore = await cookies();
  const userEmail = cookieStore.get("scada_email")?.value;

  // Si el correo no es el del administrador, lo expulsamos a la página principal ("/")
  if (userEmail !== "administrador@acfarma.com") {
    redirect("/"); 
  }

  // --- 2. CARGA DE DATOS ---
  // Si el código llega hasta aquí, significa que ES el administrador.
  // Ahora sí, cargamos la lista de usuarios.
  const users = await userService.getUsers();

  return (
    <div className="flex flex-col items-center w-full">
      <h1 className="text-3xl font-bold mb-8 text-emerald-400">
        Gestión de Usuarios
      </h1>

      <div className="w-full flex flex-col xl:flex-row gap-8 justify-center items-start">
        {/* Columna Izquierda: Crear */}
        <div className="w-full xl:w-1/3 flex justify-center">
          <UserForm />
        </div>

        {/* Columna Derecha: Listar */}
        <div className="w-full xl:w-2/3 grid gap-4 grid-cols-1 md:grid-cols-2">
          {users.length > 0 ? (
            users.map((user) => (
              <UserCard key={user.id} user={user} />
            ))
          ) : (
            <p className="text-gray-500 text-center col-span-2">No hay operadores.</p>
          )}
        </div>
      </div>
    </div>
  );
}