// src/services/mlopsService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface ModelMetrics {
    version_tag: string;
    r2_score: number;
    rmse: number;
    batch_id: string | null;
    trained_at: string;
    status: string;
}

export interface ModelHistoryResponse {
    status: string;
    data: ModelMetrics[];
    total_models: number;
}

export const mlopsService = {
    async getActiveModelMetrics(): Promise<ModelMetrics> {
        const res = await fetch(`${API_URL}/mlops/metrics`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error recuperando métricas del Champion.");
        return res.json();
    },

    async getModelHistory(): Promise<ModelHistoryResponse> {
        const res = await fetch(`${API_URL}/mlops/history`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error cargando el Model Registry.");
        return res.json();
    },

    async triggerRetraining(): Promise<{ status: string; message: string; version_tag?: string }> {
        const res = await fetch(`${API_URL}/mlops/retrain`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || "Fallo crítico en el pipeline MLOps");
        }
        return res.json();
    }
};