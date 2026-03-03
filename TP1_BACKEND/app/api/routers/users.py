from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
# Importamos nuestro nuevo servicio
import app.services.user_service as UserService 

router = APIRouter(prefix="/users", tags=["users"])

# --- El Router (El Mesero) ---

@router.get("/", response_model=List[UserResponse])
def read_users(db: Session = Depends(get_db)):
    # El router solo "llama" al servicio
    return UserService.get_all_users(db)

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return UserService.create_user(db, user)

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    updated_user = UserService.update_user(db, user_id, user_update)
    
    # El router decide qué respuesta HTTP dar según el resultado
    if not updated_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return updated_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    is_deleted = UserService.delete_user(db, user_id)
    
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    return {"mensaje": f"Usuario {user_id} eliminado"}