# app/schemas/user.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.models.users_model import UserRole

# Base común (campos compartidos)
class UserBase(BaseModel):
    username: str
    full_name: str
    role: UserRole

# DTO para crear (Input) - similar a UserCreationDTO
class UserCreate(UserBase):
    password: str
    
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    

class UserResponse(UserBase):
    id: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


UserCreate.model_rebuild()
