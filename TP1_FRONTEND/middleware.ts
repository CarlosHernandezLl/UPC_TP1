import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // 1. Extraemos el token guardado en las cookies de forma nativa
  const token = request.cookies.get('scada_token')?.value;
  const { pathname } = request.nextUrl;

  // 2. Salvaguarda explícita dentro de la función:
  // Si el usuario ya va hacia el login, no ejecutes ninguna lógica para evitar bucles infinitos
  if (pathname.startsWith('/login')) {
    return NextResponse.next();
  }

  // 3. Si el operador NO tiene token y está intentando acceder a una ruta protegida
  if (!token) {
    // 💡 CRUCIAL PARA VERCEL: Usar request.nextUrl en lugar de request.url asegura 
    // que la URL absoluta se construya perfectamente respetando los proxies de la nube.
    const loginUrl = new URL('/login', request.nextUrl);
    return NextResponse.redirect(loginUrl);
  }

  // 4. Si hay token, permitimos el acceso al SCADA web
  return NextResponse.next();
}

// 🎯 EL MATCHER INMUNE A ERRORES DE INSTANCIA (Estándar de Next.js)
export const config = {
  matcher: [
    /*
     * Excluye explícitamente rutas que rompen el Edge Runtime de Vercel:
     * - api: Rutas de endpoints internos o Server Actions de Next.js
     * - _next/static: Archivos CSS, JS empaquetados por Turbopack
     * - _next/image: Filtros de optimización de imágenes nativos
     * - Archivos estáticos directos de la carpeta public (favicon, logos, etc.)
     */
    '/((?!api|_next/static|_next/image|favicon.ico|manifest.json|robots.txt).*)',
  ],
};