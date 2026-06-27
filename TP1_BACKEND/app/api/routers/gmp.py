from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.gmp_schema import GmpParameterUpdate, GmpParameterResponse
from app.services.gmp_service import GmpService
from app.services.audit_service import AuditService
from app.repositories.gmp_repository import GmpRepository
from app.repositories.audit_repository import AuditRepository
from app.api.deps import get_current_user
from app.models.users_model import UserRole

router = APIRouter(prefix="/config/gmp", tags=["config"])

@router.get("/", response_model=GmpParameterResponse)
def get_gmp_parameters(
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)):
    
    repo = GmpRepository(db)
    params = repo.get_current_parameters()

    if not params:
        return {
            "id": 0,
            "min_hum_limit": 40.0,
            "max_hum_limit": 70.0,
            "default_setpoint": 50.0,
            "updated_at": datetime.now(),
            "updated_by": None
        }
        raise HTTPException(status_code=404, detail="No se han configurado parámetros iniciales")
    return params

@router.put("/", response_model=GmpParameterResponse)
def update_gmp_parameters(
    data: GmpParameterUpdate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación rechazada: Solo el perfil Administrador de Planta puede alterar los límites GMP."
        )
        
    repo = GmpRepository(db)
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    service = GmpService(repo, audit_service)
    
    clean_data = data.model_dump(exclude_none=True)
    
    return service.update_gmp_config(current_user.id, clean_data)