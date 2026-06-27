// src/services/aiService.ts

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Función auxiliar para el token
const getAuthToken = (): string => {
  if (typeof window === "undefined") return "";
  const value = `; ${document.cookie}`;
  const parts = value.split(`; scada_token=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift() || "";
  return "";
};

// --- INTERFACES ---

export interface SimulationRequest {
  temp_ext: number;
  hum_ext: number;
  temp_uma: number;
  hum_uma: number;
  potencia_actual: number;
  hum_sala_actual: number;
  setpoint_humedad: number;
}

export interface SimulationResponse {
  potencia_recomendada: number;
  ahorro_estimado_pct: number;
  alerta_gmp: boolean;
  explicacion_gemini?: string; // Para la integración con Vertex AI
}

export interface OptimizationLogPayload {
  temp_ext: number;
  hum_ext: number;
  temp_uma: number;
  hum_uma: number;
  hum_sala_actual: number;
  setpoint_humedad: number;
  potencia_actual: number;
  potencia_recomendada: number;
  potencia_aplicada: number;
  accion: string;
  justificacion: string | null;
}

export interface MLOpsTrainingLog {
  version: string;
  triggered_by: string;
  r2_score: number;
  date: string;
}

export interface ModelMetrics {
  r2_score: number;
  mse: number;
  version: string;
  last_trained: string;
  training_history?: MLOpsTrainingLog[];
  gmp_limits?: {
    min_humedad: number;
    max_humedad: number;
  };
}

// Estrictamente necesaria para que Dashboard.tsx funcione sin errores
export interface DashboardMetrics {
  kpi_ahorro: number;
  kpi_diferencial: number;
  r2_score: number | string;
  auditData: { time: string; real: number; ideal: number }[];
  modelCorrelation: { hum: number; pwr: number }[];
}

export const aiService = {
  // 1. Para Simulator.tsx: Pide recomendación al XGBoost
  async predictPower(data: SimulationRequest): Promise<SimulationResponse> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/ai/predict`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!res.ok) throw new Error("Error al consultar el modelo de IA");
    return await res.json();
  },

  // 2. Para Simulator.tsx: Guarda en auditoría la decisión exacta del operador
  async logOperatorAction(payload: OptimizationLogPayload): Promise<void> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/ai/log-action`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload), // Mandamos el snapshot completo
    });

    if (!res.ok) throw new Error("Fallo al registrar la telemetría en el servidor");
  },

  // 3. Para IAControl.tsx: Dispara el reentrenamiento
  async triggerTraining(): Promise<ModelMetrics> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/ai/train`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (!res.ok) throw new Error("Fallo en el reentrenamiento del modelo");
    return await res.json();
  },

  // 4. Para Dashboard.tsx: Trae los datos reales para las gráficas
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const token = getAuthToken();
    const res = await fetch(`${API_URL}/ai/dashboard-metrics`, {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` }
    });

    if (!res.ok) throw new Error("Error cargando métricas del dashboard");
    return await res.json();
  },

  async getModelPerformanceMetadata(): Promise<ModelMetrics> {
    const token = getAuthToken();

    const [metaRes, gmpRes] = await Promise.all([
      fetch(`${API_URL}/ai/metrics`, { headers: { "Authorization": `Bearer ${token}` } }),
      fetch(`${API_URL}/config/gmp/`, { headers: { "Authorization": `Bearer ${token}` } })
    ]);

    if (!metaRes.ok) {
      const errorData = await metaRes.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${metaRes.status} en el servicio de métricas analíticas de IA.`);
    }

    if (!gmpRes.ok) {
      const errorData = await gmpRes.json().catch(() => ({}));
      throw new Error(errorData.detail || `Error ${gmpRes.status} al consultar la configuración de umbrales GMP.`);
    }

    const metaData = await metaRes.json();
    const gmpData = await gmpRes.json();

    return {
      ...metaData,
      gmp_limits: {
        min_humedad: gmpData.min_hum_limit,
        max_humedad: gmpData.max_hum_limit
      }
    };
  },

  async updateGmpLimits(limits: { min_humedad: number; max_humedad: number }): Promise<any> {
    const token = getAuthToken();

    const res = await fetch(`${API_URL}/config/gmp/`, {
      method: "PUT",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        min_hum_limit: limits.min_humedad,
        max_hum_limit: limits.max_humedad
      })
    });

    if (!res.ok) {
      if (res.status === 403) throw new Error("No tienes permisos de Administrador para esta acción.");
      throw new Error("Error al persistir las restricciones regulatorias.");
    }
    return await res.json();
  },

};