// src/services/dataService.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface IngestionLog {
  id: number;
  fecha_carga: string;
  rango_datos: string;
  registros: number;
  estado: string;
}

const getAuthToken = (): string => {
  if (typeof window === "undefined") return ""; // Evita fallos en Server-Side Rendering
  const value = `; ${document.cookie}`;
  const parts = value.split(`; scada_token=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || "";
  return "";
};

export const dataService = {
  async getIngestionHistory(): Promise<IngestionLog[]> {

    const token = getAuthToken();
    if (!token) {
      throw new Error("No se encontró el token de autenticación");
    }
    const res = await fetch(`${API_URL}/data/ingestion/history`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      }
    });

    if (!res.ok) {
      if (res.status === 401) throw new Error("Sesión expirada o no autorizada");
      throw new Error("Error al obtener el historial de ingesta");
    }
    return await res.json();
  },

  async uploadHvacData(
    filePlc: File,
    fileLog: File,
    fileExt: File,
    startDate?: string,
    endDate?: string
  ) {
    const token = getAuthToken();
    const formData = new FormData();

    formData.append("file_plc", filePlc);
    formData.append("file_log", fileLog);
    formData.append("file_ext", fileExt);

    if (startDate) formData.append("start_date", startDate);
    if (endDate) formData.append("end_date", endDate);

    const res = await fetch(`${API_URL}/data/upload`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}` // 🔑 Inyección del token de seguridad
        // NOTA: Al usar FormData, NO debes poner "Content-Type", el navegador lo calcula solo.
      },
      body: formData,
    });

    if (!res.ok) {
      if (res.status === 401) throw new Error("No tienes permisos de Administrador para esta acción");
      throw new Error("Error en el procesamiento del dataset en el servidor");
    }

    return await res.json();
  }
};