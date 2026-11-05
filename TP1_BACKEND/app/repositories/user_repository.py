from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_username_ci(self, username: str) -> User | None:
        """Búsqueda sin distinguir mayúsculas/minúsculas ni espacios laterales."""
        return (
            self.db.query(User)
            .filter(func.lower(User.username) == username.strip().lower())
            .first()
        )

    def get_by_full_name_ci(self, full_name: str) -> User | None:
        return (
            self.db.query(User)
            .filter(func.lower(func.trim(User.full_name)) == full_name.strip().lower())
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user_data: dict, hashed_password: str) -> User:
        db_user = User(
            username=user_data["username"],
            hashed_password=hashed_password,
            full_name=user_data.get("full_name"),
            role=user_data["role"],
            is_active=True,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user_id: int, update_data: dict) -> User | None:
        db_user = self.get_by_id(user_id)
        if db_user:
            for key, value in update_data.items():
                setattr(db_user, key, value)
            self.db.commit()
            self.db.refresh(db_user)
        return db_user

    def soft_delete(self, user_id: int) -> User | None:
        db_user = self.get_by_id(user_id)
        if db_user:
            db_user.is_active = False
            self.db.commit()
            self.db.refresh(db_user)
        return db_user
