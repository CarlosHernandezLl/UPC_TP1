# app/schemas/user.py
from pydantic import BaseModel
from typing import Optional

# Base común (campos compartidos)
class UserBase(BaseModel):
    email: str
    nombre: str
    activo: bool = True

# DTO para crear (Input) - similar a UserCreationDTO
class UserCreate(UserBase):
    password: str

# DTO para responder (Output) - similar a UserResponseDTO
class UserResponse(UserBase):
    id: int
    
    # Esta configuración es clave para que Pydantic lea datos de un ORM (como Hibernate/JPA)
    class Config:
        from_attributes = True

class UserUpdate(UserBase):
    email: Optional[str] = None
    nombre: Optional[str] = None
    activo: Optional[bool] = True
