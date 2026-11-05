// src/services/auditService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface AuditLog {
    id: number;
    action: string;
    user: string;
    timestamp: string;
    details: string;
}

const rangeQuery = (desde?: string, hasta?: string) => {
    const params = new URLSearchParams();
    if (desde) params.set("desde", desde);
    if (hasta) params.set("hasta", hasta);
    const qs = params.toString();
    return qs ? `?${qs}` : "";
};

const authHeaders = () => ({ "Authorization": `Bearer ${getAuthToken()}` });

const failWithDetail = async (res: Response, fallback: string): Promise<never> => {
    const body = await res.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : fallback);
};

export const auditService = {
    async getAuditLogs(desde?: string, hasta?: string): Promise<AuditLog[]> {
        const res = await fetch(`${API_URL}/audit/${rangeQuery(desde, hasta)}`, { headers: authHeaders() });
        if (!res.ok) return failWithDetail(res, "Error cargando el Audit Trail");
        return res.json();
    },

    async logManualAction(action: string, detail: string): Promise<void> {
        const res = await fetch(`${API_URL}/audit/log`, {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ action, detail })
        });
        if (!res.ok) throw new Error("Error registrando log manual");
    },

    async exportCsv(desde?: string, hasta?: string): Promise<Blob> {
        const res = await fetch(`${API_URL}/audit/export-applied-csv${rangeQuery(desde, hasta)}`, { headers: authHeaders() });
        if (!res.ok) return failWithDetail(res, "Error descargando CSV");
        return res.blob();
    },

    async exportPdf(desde?: string, hasta?: string): Promise<Blob> {
        const res = await fetch(`${API_URL}/audit/export-applied-pdf${rangeQuery(desde, hasta)}`, { headers: authHeaders() });
        if (!res.ok) return failWithDetail(res, "Error descargando PDF");
        return res.blob();
    }
};
