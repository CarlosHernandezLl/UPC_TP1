// src/services/auditService.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL;
const getAuthToken = () => typeof window !== "undefined" ? `; ${document.cookie}`.split(`; scada_token=`).pop()?.split(';').shift() || "" : "";

export interface AuditLog {
    id: number;
    action: string;
    resource: string;
    user_full_name: string;
    timestamp: string;
    detail: string;
}

export const auditService = {
    async getAuditLogs(): Promise<AuditLog[]> {
        const res = await fetch(`${API_URL}/audit/`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error cargando el Audit Trail");
        return res.json();
    },

    async logManualAction(action: string, detail: string): Promise<void> {
        const res = await fetch(`${API_URL}/audit/log`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${getAuthToken()}` },
            body: JSON.stringify({ action, detail })
        });
        if (!res.ok) throw new Error("Error registrando log manual");
    },

    async exportCsv(): Promise<Blob> {
        const res = await fetch(`${API_URL}/audit/export-applied-csv`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error descargando CSV");
        return res.blob();
    },

    async exportPdf(): Promise<Blob> {
        const res = await fetch(`${API_URL}/audit/export-applied-pdf`, {
            headers: { "Authorization": `Bearer ${getAuthToken()}` }
        });
        if (!res.ok) throw new Error("Error descargando PDF");
        return res.blob();
    }
};