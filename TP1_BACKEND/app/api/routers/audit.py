from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.audit_schema import AuditCreate, AuditResponse
from app.services.audit_service import AuditService

from app.repositories.audit_repository import AuditRepository
from app.api.deps import get_current_user, check_role

router = APIRouter(prefix="/audit", tags=["audit"])


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    return audit_service


@router.get(
    "/",
    response_model=List[AuditResponse],
    dependencies=[Depends(check_role(["AUDITOR", "ADMIN"]))],
)
def get_audit_trail(service: AuditService = Depends(get_audit_service)):
    return service.get_report_data()


@router.post("/log")
def log_operator_decision(
    payload: AuditCreate,
    service: AuditService = Depends(get_audit_service),
    current_user: any = Depends(get_current_user),
):
    service.record_action(
        user_id=current_user.id,
        action=payload.action,
        resource="MANUAL_AUDIT",
        detail=payload.detail,
    )
    return {
        "status": "success",
        "message": "Acción registrada en la pista de auditoría GxP.",
    }


@router.get(
    "/export-applied-csv",
    dependencies=[Depends(check_role(["AUDITOR", "ADMIN"]))],
)
def export_applied_recommendations_csv(
    service: AuditService = Depends(get_audit_service),
):
    """Genera y transmite un reporte CSV con la telemetría de recomendaciones acatadas."""
    try:
        csv_buffer = service.export_applied_recommendations_csv()
        headers = {
            "Content-Disposition": 'attachment; filename="reporte_gxp_recomendaciones_aplicadas.csv"'
        }
        return StreamingResponse(csv_buffer, media_type="text/csv", headers=headers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte CSV: {str(e)}",
        )


@router.get(
    "/export-applied-pdf",
    dependencies=[Depends(check_role(["AUDITOR", "ADMIN"]))],
)
def export_applied_recommendations_pdf(
    service: AuditService = Depends(get_audit_service),
):
    """Genera y transmite un reporte PDF con firma digital sobre las recomendaciones aplicadas."""
    try:
        pdf_buffer = service.export_applied_recommendations_pdf()
        headers = {
            "Content-Disposition": 'attachment; filename="reporte_gxp_recomendaciones_aplicadas.pdf"'
        }
        return StreamingResponse(
            pdf_buffer, media_type="application/pdf", headers=headers
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando reporte PDF: {str(e)}",
        )
