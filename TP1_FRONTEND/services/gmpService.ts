// src/services/gmpService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface GmpConfig {
    min_hum_limit: number;
    max_hum_limit: number;
}

export const gmpService = {
    async getGmpParameters(): Promise<GmpConfig> {
        const res = await fetch(`${API_URL}/config/gmp/`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error al consultar la configuración GMP");
        return res.json();
    },

    async updateGmpLimits(limits: GmpConfig): Promise<GmpConfig> {
        const res = await fetch(`${API_URL}/config/gmp/`, {
            method: "PUT",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getAuthToken()}` },
            body: JSON.stringify(limits)
        });
        if (!res.ok) throw new Error("Error al persistir restricciones GMP");
        return res.json();
    }
};