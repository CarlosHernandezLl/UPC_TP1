import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Buscamos nuestra cookie
  const token = request.cookies.get('scada_token')?.value;

  // Si intentamos ir a cualquier ruta y NO hay token
  if (!token) {
    // Redirigir al login
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Si hay token, lo dejamos pasar
  return NextResponse.next();
}

// Aquí definimos qué rutas queremos proteger.
// Protegemos TODO, excepto el login, la API interna de Next, y archivos estáticos.
export const config = {
  matcher: [
    '/((?!login|_next/static|_next/image|favicon.ico).*)',
  ],
};