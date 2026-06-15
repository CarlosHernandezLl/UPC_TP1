import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Salvaguarda para recursos estáticos e internos
  if (
    pathname.startsWith('/_next') || 
    pathname.startsWith('/api') || 
    pathname.includes('.') ||
    pathname.startsWith('/login')
  ) {
    return NextResponse.next();
  }

  const token = request.cookies.get('scada_token')?.value;

  // 2. Redirección blindada para Vercel
  if (!token) {
    // Clonamos de forma segura el objeto de navegación interno de Next.js
    const url = request.nextUrl.clone();
    url.pathname = '/login'; // Mutamos la ruta hacia el login de forma limpia
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|manifest.json|robots.txt).*)',
  ],
};