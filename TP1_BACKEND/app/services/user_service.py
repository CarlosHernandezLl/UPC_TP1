from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate):
        data = user_data.model_dump()
        data["username"] = data["username"].strip()
        data["full_name"] = data["full_name"].strip()

        if self.repository.get_by_username_ci(data["username"]):
            raise ValueError("El nombre de usuario ya está registrado.")
        if self.repository.get_by_full_name_ci(data["full_name"]):
            raise ValueError("Ya existe un usuario con ese nombre completo.")

        hashed_pwd = get_password_hash(user_data.password)
        return self.repository.create(data, hashed_pwd)

    def update_user(self, user_id: int, user_data: UserUpdate):
        data = user_data.model_dump(exclude_unset=True)

        if data.get("full_name"):
            data["full_name"] = data["full_name"].strip()
            other = self.repository.get_by_full_name_ci(data["full_name"])
            if other and other.id != user_id:
                raise ValueError("Ya existe un usuario con ese nombre completo.")

        if "password" in data:
            data["hashed_password"] = get_password_hash(data.pop("password"))

        return self.repository.update(user_id, data)

    def get_by_username(self, username):
        return self.repository.get_by_username(username)

    def get_all_users(self):
        return self.repository.get_all()

    def remove_user(self, user_id: int):
        # 🛡️ GxP Compliance: Nunca borramos en SQL, desactivamos la cuenta (Soft Delete)
        return self.repository.soft_delete(user_id)
