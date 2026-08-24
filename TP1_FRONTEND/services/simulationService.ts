// src/services/simulationService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface SimulationPredictRequest {
    outdoor_temp: number;
    outdoor_rh: number;
    ahu_temp: number;
    ahu_rh: number;
    current_room_rh?: number;
    target_setpoint: number;
    current_power: number;
}

export interface SimulationPredictResponse {
    potencia_recomendada: number;
    ahorro_estimado_pct: number;
    alerta_gmp: boolean;
    explicacion_gemini: string;
}

export interface SimulationLogRequest extends SimulationPredictRequest {
    recommended_power: number;
    applied_power: number;
    action: "RECOMMENDATION_APPLIED" | "RECOMMENDATION_OVERRIDDEN";
    justification?: string;
}

export const simulationService = {
    async predictPower(data: SimulationPredictRequest): Promise<SimulationPredictResponse> {
        const res = await fetch(`${API_URL}/simulation/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getAuthToken()}` },
            body: JSON.stringify(data),
        });
        if (!res.ok) throw new Error("Error al consultar el Gemelo Digital");
        return res.json();
    },

    async logOperatorAction(payload: SimulationLogRequest): Promise<void> {
        const res = await fetch(`${API_URL}/simulation/log-action`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getAuthToken()}` },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error("Fallo al auditar la decisión operativa GxP");
    }
};