import io
import csv
from sqlalchemy.orm import Session
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from app.api.deps import get_current_user
from app.core.database import get_db

from app.schemas.audit_schema import AuditCreate, AuditResponse
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository
from app.models.optimization_model import OptimizationLog

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/", response_model=List[AuditResponse])
def get_audit_trail(db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    service = AuditService(repo)
    return service.get_report_data()


@router.post("/log")
def log_operator_decision(
    payload: AuditCreate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user) # Extrae irrefutablemente el usuario logueado
):
    repo = AuditRepository(db)
    service = AuditService(repo)
    
    # Mandamos los datos limpios al servicio
    service.register_operator_action(
        user_id=current_user.id,
        action=payload.action,
        detail=payload.detail
    )
    return {"status": "success", "message": "Acción registrada en la pista de auditoría GxP."}

@router.get("/export-applied-csv")
def export_applied_recommendations(
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    """Genera y transmite un reporte CSV con la telemetría de recomendaciones acatadas"""
    try:
        # 1. Consultar únicamente las recomendaciones aplicadas en orden cronológico
        logs = db.query(OptimizationLog).filter(
            OptimizationLog.accion == "RECOMENDACION_APLICADA"
        ).order_by(OptimizationLog.timestamp.desc()).all()

        # 2. Crear un buffer de memoria para escribir el CSV sin guardar archivos físicos en Render
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';') # Delimitador ';' ideal para Excel en español

        # 3. Escribir la cabecera del reporte (Nombres limpios para auditoría)
        writer.writerow([
            "ID_LOG", "TIMESTAMP_UTC", "ID_OPERADOR", "TEMP_EXT_C", "HUM_EXT_PCT", 
            "TEMP_UMA_C", "HUM_UMA_PCT", "HUM_SALA_ACTUAL_PCT", "SETPOINT_OBJETIVO_PCT", 
            "POTENCIA_PREVIA_PCT", "POTENCIA_RECOMENDADA_IA_PCT", "POTENCIA_APLICADA_PLC_PCT"
        ])

        # 4. Inyectar las filas con la telemetría exacta de Supabase
        for log in logs:
            writer.writerow([
                log.id,
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.user_id,
                log.temp_ext,
                log.hum_ext,
                log.temp_uma,
                log.hum_uma,
                log.hum_sala_actual,
                log.setpoint_humedad,
                log.potencia_actual,
                log.potencia_recomendada,
                log.potencia_aplicada
            ])

        # 5. Resetear el puntero del buffer de texto
        output.seek(0)

        # 6. Retornar el archivo como un Stream descargable nativamente por el navegador
        headers = {
            'Content-Disposition': 'attachment; filename="reporte_gxp_recomendaciones_aplicadas.csv"'
        }
        return StreamingResponse(output, media_type="text/csv", headers=headers)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte de auditoría: {str(e)}"
        )