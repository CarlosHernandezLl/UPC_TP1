from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService
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
    service = UserService(repo)
    
    audit_repo = AuditRepository(db)  # ⬅️ Instanciamos el repositorio de auditoría
    audit_service = AuditService(audit_repo)
    
    db_user = service.create_user(user)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="El nombre de usuario ya está registrado"
        )
    
    audit_service.record_action(
        user_id=current_user.id,
        action="USER_CREATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Creación del usuario '{db_user.username}' con rol {db_user.role.value}. Nombre completo: {db_user.full_name}."
    )
    
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: any = Depends(get_current_user)
):
    repo = UserRepository(db)
    service = UserService(repo)
    
    audit_repo = AuditRepository(db)
    audit_service = AuditService(audit_repo)
    
    updated_user = service.update_user(user_id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )
        
    clean_changes = user_update.model_dump(mode='json', exclude_unset=True)
    
    audit_service.record_action(
        user_id=current_user.id,
        action="USER_MODIFICATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Actualización del usuario '{updated_user.username}' con rol {updated_user.role.value}. Nombre completo: {updated_user.full_name}."
    )
        
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
    
    target_user = repo.get_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Usuario no encontrado"
        )
    
    target_user.is_active = False
    db.commit()
    
    audit_log = AuditTrail(
        user_id=current_user.id,
        action="USER_REVOCATION",
        resource="SECURITY_MANAGEMENT",
        detail=f"Inhabilitación de accesos (Soft Delete) para el usuario: '{target_user.username}' con rol {target_user.role.value}."    )
    audit_repo.create_log(audit_log)
    
    return {"mensaje": f"Usuario con ID {user_id} eliminado exitosamente"}