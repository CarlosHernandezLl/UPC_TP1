// src/services/dataService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface IngestionLog {
  id: number;
  batch_id: string;
  ingested_at: string;
  data_range: string;
  record_count: number;
  status: string;
}

export const dataService = {
  async getIngestionHistory(): Promise<IngestionLog[]> {
    const res = await fetch(`${API_URL}/data/ingestion/history`, {
      headers: { "Authorization": `Bearer ${getAuthToken()}` }
    });
    if (!res.ok) throw new Error("Error al obtener historial de ingesta");
    return res.json();
  },

  async uploadHvacData(filePlc: File, fileLog: File, fileExt: File, startDate?: string, endDate?: string) {
    const formData = new FormData();
    formData.append("file_plc", filePlc);
    formData.append("file_log", fileLog);
    formData.append("file_ext", fileExt);
    if (startDate) formData.append("start_date", startDate);
    if (endDate) formData.append("end_date", endDate);

    const res = await fetch(`${API_URL}/data/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${getAuthToken()}` },
      body: formData,
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({}));
      throw new Error(typeof error.detail === "string" ? error.detail : "Error en el procesamiento del dataset");
    }
    return res.json();
  }
};