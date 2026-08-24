// src/services/dashboardService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface DashboardMetrics {
    kpi_ahorro: number;
    kpi_diferencial: number;
    r2_score: number | string;
    auditData: { sample_id: string; real: number; ideal: number }[];
    modelCorrelation: { hum: number; pwr: number }[];
}

export const dashboardService = {
    async getDashboardMetrics(): Promise<DashboardMetrics> {
        const res = await fetch(`${API_URL}/dashboard/metrics`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error cargando analítica de planta");
        return res.json();
    }
};