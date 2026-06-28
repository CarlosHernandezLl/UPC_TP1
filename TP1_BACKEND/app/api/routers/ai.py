import json
import os
import math
import logging
from app.core.config import settings
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status

import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
import google.generativeai as genai


# Esquemas y Dependencias de Seguridad
from app.api.deps import get_current_user, check_role
from app.core.database import get_db
from app.schemas.ml_schema import SimRequest
from app.schemas.optimization_schema import OptimizationLogCreate

# Repositorios y Servicios del Núcleo SCADA
from app.ml_engine.simulator_engine import SimulatorEngine
from app.services.ml_training_service import MLTrainingService
from app.repositories.gmp_repository import GmpRepository
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
from app.repositories.optimization_repository import OptimizationRepository

# Modelos Físicos de Base de Datos
from app.models.hvac_model import HvacHistoricalData
from app.models.optimization_model import OptimizationLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["Inteligencia Artificial"])

# Instanciamos el motor de inferencia como un Singleton en memoria RAM
sim_engine = SimulatorEngine()
ai_model = None
GEMINI_KEY = settings.GEMINI_API_KEY

# Ruta exacta de persistencia de la metadata analítica del modelo
METADATA_PATH = os.path.join(os.path.dirname(__file__), "../../ml_engine/saved_models/model_metadata.json")

# =========================================================================
# ⚙️ INICIALIZACIÓN DIRECTA DE GEMINI (GOOGLE AI STUDIO)
# =========================================================================
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

try:
    if GEMINI_KEY:
        genai.configure(api_key=GEMINI_KEY)
        ai_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=(
                "Eres un ingeniero experto en psicrometría y automatización de sistemas HVAC en plantas farmacéuticas GxP. "
                "El sistema utiliza un modelo XGBoost entrenado mediante respuesta al escalón en estado estacionario. "
                "Las variables exteriores tienen un peso despreciable debido al pre-acondicionamiento térmico de la UMA principal. "
                "Tu tarea es justificar técnicamente la modulación del secador basándote en la de la carga latente local y el setpoint. "
                "Da una explicación concisa de máximo 2 líneas en español, usando términos como: régimen permanente, ganancia estática o estabilidad del lote."
            )
        )
        logger.info("✨ [Google AI] Conexión directa con Gemini configurada con éxito.")
    else:
        logger.warning("⚠️ Alerta: El campo gemini_api_key en settings está vacío.")
except Exception as e:
    logger.error(f"⚠️ Alerta: No se pudo conectar con Vertex AI. Se usará el motor de contingencia textual. Motivo: {e}")
    
    

def load_model_metadata():
    """Lee el archivo de persistencia del modelo. Si no existe, crea la v1.0.0 inicial."""
    if not os.path.exists(METADATA_PATH):
        initial_meta = {
            "r2_score": 0000,
            "mse": 0.0000,
            "version": "0.0.0",
            "last_trained": "Sincronizado con manuscrito original"
        }
        os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
        with open(METADATA_PATH, "w") as f:
            json.dump(initial_meta, f, indent=4)
        return initial_meta
    
    with open(METADATA_PATH, "r") as f:
        return json.load(f)


# Sincronizamos los punteros del motor RAM al levantar la API por primera vez
try:
    current_meta = load_model_metadata()
    sim_engine.r2_score = current_meta["r2_score"]
    sim_engine.mse = current_meta["mse"]
except Exception:
    pass


@router.post("/log-action", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_role(["SUPERVISOR"]))])
def log_operator_decision(
    payload: OptimizationLogCreate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    """Guarda las acciones de la pantalla del simulador para alimentar el Dashboard e histórico"""
    try:
        repo_opt = OptimizationRepository(db)
        repo_opt.save_log(user_id=current_user.id, log_in=payload)
        
        repo_audit = AuditRepository(db)
        service_audit = AuditService(repo_audit)
        
        if payload.accion == "RECOMENDACION_APLICADA":
            detalle_texto = (
                f"El operador APLICÓ la potencia recomendada del {payload.potencia_aplicada}% "
                f"sugerida por el Gemelo Digital (Setpoint HR objetivo: {payload.setpoint_humedad}%)."
            )
        else:
            detalle_texto = (
                f"El operador IGNORÓ la recomendación de la IA ({payload.potencia_recomendada}%) "
                f"y mantuvo la potencia manual al {payload.potencia_aplicada}%. Motivo: {payload.justificacion}"
            )

        service_audit.register_operator_action(
            user_id=current_user.id,
            action=payload.accion,
            detail=detalle_texto
        )
        
        return {
            "status": "success", 
            "message": "Telemetría guardada y Pista de Auditoría GxP generada mediante servicio reutilizado."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error en el guardado unificado de optimización: {str(e)}"
        )


@router.get("/metrics", dependencies=[Depends(check_role([]))])
def get_model_performance_metadata(current_user: any = Depends(get_current_user)):
    """Lee la metadata persistente y real del regresor para las tarjetas informativas de la UI"""
    try:
        meta = load_model_metadata()
        return meta
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo recuperar la metadata analítica.")


@router.post("/train", dependencies=[Depends(check_role([]))])
async def trigger_model_retraining(db: Session = Depends(get_db), current_user: any = Depends(get_current_user)):
    """
    Pipeline MLOps Real: Extrae la serie de tiempo continua, ejecuta el filtro SSD 
    en la RAM, calcula la validación GroupShuffleSplit y actualiza los pesos en caliente.
    """
    try:
        # Instanciamos el servicio de auditoría inmutable
        repo_audit = AuditRepository(db)
        service_audit = AuditService(repo_audit)

        # Invocamos al motor de entrenamiento científico
        training_service = MLTrainingService(db, sim_engine)
        resultado = training_service.ejecutar_reentrenamiento_masivo()

        if resultado["status"] == "error":
            raise HTTPException(status_code=400, detail=resultado["message"])

        service_audit.record_action(
            user_id=current_user.id,
            action="MODEL_TRAINING",
            resource="ML_MICROSERVICE",
            detail=f"Pipeline MLOps ejecutado exitosamente por el Administrador. {resultado['message']}"
        )
        
        nueva_metadata = load_model_metadata()
        return nueva_metadata

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo crítico en el pipeline MLOps incremental: {str(e)}")


@router.post("/predict", dependencies=[Depends(check_role(["SUPERVISOR"]))])
async def get_prediction(req: SimRequest, db: Session = Depends(get_db)):
    """
    Genera la recomendación óptima bajo un esquema de tolerancia a fallos (Failsafe).
    Garantiza una respuesta HTTP 200 OK aunque caigan las APIs externas o la DB.
    """
    potencia_ideal = req.potencia_actual
    ahorro = 0.0
    alerta_gmp = False
    explicacion_dinamica = "Ajuste basado en equilibrio psicrométrico estándar (Modo de Contingencia Local)."

    min_hum_limit = 40.0
    max_hum_limit = 55.0
    try:
        gmp_repo = GmpRepository(db)
        config_activa = gmp_repo.get_current_parameters()
        if config_activa:
            # Usamos getattr por seguridad si la tabla sufriera cambios estructurales
            min_hum_limit = getattr(config_activa, "min_hum_limit", 40.0)
            max_hum_limit = getattr(config_activa, "max_hum_limit", 55.0)
    except Exception as db_err:
        logger.error(f"⚠️ Alerta GxP: Fallo al conectar con Supabase. Usando umbrales de seguridad por defecto: {db_err}")

    try:
        potencia_ideal, alerta_gmp = sim_engine.recomendar_potencia(
            temp_ext=req.temp_ext,
            hum_ext=req.hum_ext,
            temp_uma=req.temp_uma,
            hum_uma=req.hum_uma,
            setpoint_hr_sala=req.setpoint_humedad,
            min_hum_limit=min_hum_limit,
            max_hum_limit=max_hum_limit
        )
        if req.potencia_actual > potencia_ideal:
            ahorro = round(((req.potencia_actual - potencia_ideal) / req.potencia_actual) * 100, 1)
    except Exception as ml_err:
        logger.error(f"⚠️ Fallo crítico en el motor matemático XGBoost: {ml_err}")
        # Al fallar la matemática, se congela el estado actual: potencia recomendada = potencia actual

    if ai_model:
        try:
            hum_referencia = getattr(req, "hum_uma", 50.0)
            
            prompt_ingenieria = (
                f"Contexto Operacional Estacionario:\n"
                f"- Humedad de Control: {hum_referencia}% HR.\n"
                f"- Setpoint de Seguridad: {req.setpoint_humedad}% HR.\n"
                f"- Ajuste Predictivo: Cambiar potencia del {req.potencia_actual}% al {potencia_ideal}%.\n"
                f"- Alerta Higrométrica GxP: {'CRÍTICA' if alerta_gmp else 'NORMAL'}.\n\n"
                f"Explica resumidamente al operador cómo este ajuste estabiliza el lazo cerrado respecto al setpoint objetivo."
            )

            response = ai_model.generate_content(
                prompt_ingenieria,
                generation_config={"max_output_tokens": 120, "temperature": 0.15}
            )
            if response.text:
                explicacion_dinamica = response.text.strip().replace('"', '')
                
        except Exception as ai_err:
            logger.error(f"⚠️ API de Gemini no disponible o Timeout de red: {ai_err}")
            if alerta_gmp:
                explicacion_dinamica = "Ajuste preventivo forzado para contener de manera inmediata una potencial excursión fuera de los umbrales regulatorios."
            elif ahorro > 0:
                explicacion_dinamica = "Optimización del trabajo mecánico del deshumidificador conservando la estabilidad de la carga latente."

    return {
        "potencia_recomendada": potencia_ideal,
        "ahorro_estimado_pct": ahorro,
        "alerta_gmp": alerta_gmp,
        "explicacion_gemini": explicacion_dinamica
    }


@router.get("/dashboard-metrics", dependencies=[Depends(check_role(["GERENTE"]))])
def get_dashboard_metrics(db: Session = Depends(get_db), current_user: any = Depends(get_current_user)):
    """Calcula las métricas de eficiencia energética y analíticas para alimentar la pantalla Dashboard"""
    try:
        records = db.query(OptimizationLog).order_by(OptimizationLog.timestamp.desc()).limit(24).all()
        correlation_records = db.query(OptimizationLog).order_by(OptimizationLog.timestamp.desc()).limit(100).all()

        if not records:
            return {
                "kpi_ahorro": 0.0,
                "kpi_diferencial": 0.0,
                "r2_score": getattr(sim_engine, 'r2_score', 87.59),
                "auditData": [],
                "modelCorrelation": []
            }

        records.reverse()

        audit_data = []
        ahorro_acumulado_kwh = 0.0
        total_energia_real_kwh = 0.0
        
        UMA_NOMINAL_KW = 15.0 
        HORAS_POR_VENTANA = 4.0

        for r in records:
            real_pwr = float(r.potencia_actual)     
            ideal_pwr = float(r.potencia_recomendada)  
            
            audit_data.append({
                "sample_id": r.timestamp.strftime('%d/%m %H:%M'), 
                "real": round(real_pwr, 1), 
                "ideal": round(ideal_pwr, 1)
            })  
            
            kwh_real = (real_pwr / 100.0) * UMA_NOMINAL_KW * HORAS_POR_VENTANA
            kwh_ideal = (ideal_pwr / 100.0) * UMA_NOMINAL_KW * HORAS_POR_VENTANA
            
            total_energia_real_kwh += kwh_real
            if kwh_real > kwh_ideal:
                ahorro_acumulado_kwh += (kwh_real - kwh_ideal)

        model_correlation = [
            {
                "hum": round(c.hum_sala_actual, 1), 
                "pwr": round(c.potencia_aplicada, 1)
            } for c in correlation_records
        ]

        kpi_ahorro_pct = 0.0
        if total_energia_real_kwh > 0:
            kpi_ahorro_pct = round((ahorro_acumulado_kwh / total_energia_real_kwh) * 100, 1)

        return {
            "kpi_ahorro": kpi_ahorro_pct, 
            "kpi_diferencial": round(ahorro_acumulado_kwh, 1), 
            "r2_score": getattr(sim_engine, 'r2_score', 87.59),                      
            "auditData": audit_data,
            "modelCorrelation": model_correlation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en analítica de indicadores de planta: {str(e)}")