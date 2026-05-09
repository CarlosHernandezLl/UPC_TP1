from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.audit_schema import AuditResponse
from app.services.audit_service import AuditService
from app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/", response_model=List[AuditResponse])
def get_audit_trail(db: Session = Depends(get_db)):
    repo = AuditRepository(db)
    service = AuditService(repo)
    return service.get_report_data()