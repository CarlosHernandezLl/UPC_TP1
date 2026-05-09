from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate
from app.core.security import get_password_hash # Tu función de hashing

class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate):
        # Validación estandarizada
        if self.repository.get_by_username(user_data.username):
            return None
        
        hashed_pwd = get_password_hash(user_data.password)
        return self.repository.create(user_data, hashed_pwd)

    def update_user(self, user_id: int, user_data: UserUpdate):
        # Convertimos el esquema a diccionario eliminando los valores nulos
        data = user_data.model_dump(exclude_unset=True)
    
        # Si viene password, lo hasheamos y cambiamos el nombre a hashed_password
        if "password" in data:
            data["hashed_password"] = get_password_hash(data.pop("password"))
        
        return self.repository.update(user_id, data)

    def get_all_users(self):
        return self.repository.get_all_users()

    def remove_user(self, user_id: int):
        return self.repository.delete(user_id)