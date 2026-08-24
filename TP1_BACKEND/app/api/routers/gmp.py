from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db

from app.schemas.gmp_schema import GmpParameterUpdate, GmpParameterResponse

from app.services.gmp_service import GmpService
from app.services.audit_service import AuditService

from app.repositories.gmp_repository import GmpRepository
from app.repositories.audit_repository import AuditRepository

from app.api.deps import get_current_user, check_role

router = APIRouter(prefix="/config/gmp", tags=["config"])


def get_gmp_service(db: Session = Depends(get_db)) -> GmpService:
    gmp_repo = GmpRepository(db)
    audit_service = AuditService(AuditRepository(db))
    return GmpService(repository=gmp_repo, audit_service=audit_service)


@router.get("/", response_model=GmpParameterResponse)
def get_gmp_parameters(
    service: GmpService = Depends(get_gmp_service),
    current_user: any = Depends(get_current_user),
):
    params = service.get_active_config()
    if not params:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se han configurado parámetros GMP iniciales.",
        )
    return params


@router.put(
    "/",
    response_model=GmpParameterResponse,
    dependencies=[Depends(check_role(["ADMIN"]))],
)
def update_gmp_parameters(
    data: GmpParameterUpdate,
    service: GmpService = Depends(get_gmp_service),
    current_user: any = Depends(get_current_user),
):
    clean_data = data.model_dump(exclude_none=True)

    return service.update_gmp_config(user_id=current_user.id, config_data=clean_data)
