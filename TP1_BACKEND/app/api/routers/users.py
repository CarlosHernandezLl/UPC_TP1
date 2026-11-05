from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.api.deps import get_current_user, check_role, get_audit_service
from app.services.audit_service import AuditService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)


@router.get(
    "/",
    response_model=List[UserResponse],
    dependencies=[Depends(check_role(["ADMIN"]))],
)
def read_users(
    service: UserService = Depends(get_user_service),
    current_user: any = Depends(get_current_user),
):
    return service.get_all_users()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_role(["ADMIN"]))],
)
def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: any = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    try:
        created = service.create_user(user_data=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    audit_service.record_action(
        user_id=current_user.id,
        action="USER_CREATED",
        resource="USER_MANAGEMENT",
        detail=f"Usuario '{created.username}' creado con rol {user.role.value}.",
    )
    return created


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(check_role(["ADMIN"]))],
)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: any = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    try:
        updated_user = service.update_user(user_id=user_id, user_data=user_update)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado."
        )
    changed = sorted(user_update.model_dump(exclude_unset=True).keys())
    audit_service.record_action(
        user_id=current_user.id,
        action="USER_UPDATED",
        resource="USER_MANAGEMENT",
        detail=f"Usuario '{updated_user.username}' actualizado. Campos: {', '.join(changed)}.",
    )
    return updated_user


@router.delete("/{user_id}", dependencies=[Depends(check_role(["ADMIN"]))])
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    current_user: any = Depends(get_current_user),
    audit_service: AuditService = Depends(get_audit_service),
):
    removed_user = service.remove_user(user_id=user_id)
    if not removed_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado para inhabilitación.",
        )
    audit_service.record_action(
        user_id=current_user.id,
        action="USER_DELETED",
        resource="USER_MANAGEMENT",
        detail=f"Acceso del usuario '{removed_user.username}' revocado (baja lógica).",
    )
    return {
        "status": "success",
        "message": f"Usuario con ID {user_id} inhabilitado exitosamente.",
    }
