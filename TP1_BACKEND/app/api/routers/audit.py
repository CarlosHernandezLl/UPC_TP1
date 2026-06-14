from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.api.deps import get_current_user
from app.core.database import get_db
from app.schemas.audit_schema import AuditCreate, AuditResponse
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository

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