from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def create_user(self, user_data: UserCreate):
        if self.repository.get_by_username(user_data.username):
            return None

        hashed_pwd = get_password_hash(user_data.password)
        return self.repository.create(user_data.model_dump(), hashed_pwd)

    def update_user(self, user_id: int, user_data: UserUpdate):
        data = user_data.model_dump(exclude_unset=True)

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
