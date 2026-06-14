from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.models.audit_model import AuditTrail
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db), current_user: any = Depends(get_current_user)):
    repo = UserRepository(db)
    service = UserService(repo)
    return service.get_all_users()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)  # ⬅️ Quién está ejecutando la acción
):
    repo = UserRepository(db)
    audit_repo = AuditRepository(db)  # ⬅️ Instanciamos el repositorio de auditoría
    service = UserService(repo)
    
    db_user = service.create_user(user)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El nombre de usuario ya está registrado"
        )
    
    # 📝 REGISTRO EN EL AUDIT TRAIL
    audit_log = AuditTrail(
        user_id=current_user.id,
        action="USER_CREATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Creación del usuario '{db_user.username}' con rol {db_user.role}. Nombre completo: {db_user.full_name}."
    )
    audit_repo.create_log(audit_log)  # Usa tu función exacta del repositorio
    
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    service = UserService(repo)
    
    updated_user = service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )
    
    audit_log = AuditTrail(
        user_id=current_user.id,
        action="USER_MODIFICATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Modificación de parámetros GxP del usuario ID {user_id}. Nuevos cambios: {user_update.dict(exclude_unset=True)}."
    )
    audit_repo.create_log(audit_log)
    
    return updated_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    repo = UserRepository(db)
    audit_repo = AuditRepository(db)
    service = UserService(repo)
    
    target_user = repo.get_by_id(user_id)  # O el método que uses para buscar por ID
    username_target = target_user.username if target_user else f"ID {user_id}"

    is_deleted = service.remove_user(user_id)
    if not is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )
    
    audit_log = AuditTrail(
        user_id=current_user.id,
        action="USER_REVOCATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Revocación permanente de accesos para el identificador único: '{username_target}'."
    )
    audit_repo.create_log(audit_log)
    
    return {"mensaje": f"Usuario con ID {user_id} eliminado exitosamente"}