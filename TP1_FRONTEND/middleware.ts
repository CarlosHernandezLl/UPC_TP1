import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. SALVAGUARDA DE AMBIENTE: Omitir inmediatamente archivos del sistema, imágenes y recursos
  // Esto evita que Vercel intente evaluar scripts internos de empaquetado o fuentes.
  if (
    pathname.startsWith('/_next') || 
    pathname.startsWith('/api') || 
    pathname.includes('.') ||
    pathname.startsWith('/login')
  ) {
    return NextResponse.next();
  }

  // 2. Extracción nativa de la cookie (Sin usar ninguna librería externa)
  const token = request.cookies.get('scada_token')?.value;

  // 3. Control estricto de acceso GxP para producción
  if (!token) {
    // Forzamos la URL absoluta utilizando el nextUrl parseado por la infraestructura de Vercel
    const loginUrl = new URL('/login', request.nextUrl);
    return NextResponse.redirect(loginUrl);
  }

  // 4. Si el token existe, se autoriza el paso al SCADA web
  return NextResponse.next();
}

// 🎯 MATCHER OFICIAL DE ALTA RESILIENCIA
export const config = {
  matcher: [
    /*
     * Intercepta todas las rutas de la aplicación excepto los recursos críticos
     * de compilación estática que hacen fallar el Edge Runtime.
     */
    '/((?!api|_next/static|_next/image|favicon.ico|manifest.json|robots.txt).*)',
  ],
};