from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.gmp_schema import GmpParameterUpdate, GmpParameterResponse
from app.services.gmp_service import GmpService
from app.services.audit_service import AuditService
from app.repositories.gmp_repository import GmpRepository
from app.repositories.audit_repository import AuditRepository

router = APIRouter(prefix="/config/gmp", tags=["config"])

@router.get("/", response_model=GmpParameterResponse)
def get_gmp_parameters(db: Session = Depends(get_db)):
    repo = GmpRepository(db)
    params = repo.get_current_parameters()
    if not params:
        raise HTTPException(status_code=404, detail="No se han configurado parámetros iniciales")
    return params

@router.put("/", response_model=GmpParameterResponse)
def update_gmp_parameters(
    data: GmpParameterUpdate, 
    db: Session = Depends(get_db),
    # Aquí deberías obtener el user_id del token JWT en el futuro
    current_user_id: int = 1
):
    repo = GmpRepository(db)
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    service = GmpService(repo, audit_service)
    
    return service.update_gmp_config(current_user_id, data.model_dump())