import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Evita que el navegador sirva páginas protegidas desde caché (bfcache / botón Atrás) tras cerrar sesión
  async headers() {
    return [
      {
        source: "/((?!_next/static|_next/image|favicon.ico).*)",
        headers: [
          { key: "Cache-Control", value: "no-store, no-cache, must-revalidate, max-age=0" },
          { key: "Pragma", value: "no-cache" },
        ],
      },
    ];
  },
};

export default nextConfig;
