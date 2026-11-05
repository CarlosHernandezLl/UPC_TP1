from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.user import UserRole

class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    full_name: str = Field(..., min_length=3, max_length=100)
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Contraseña segura de mínimo 8 caracteres")

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)