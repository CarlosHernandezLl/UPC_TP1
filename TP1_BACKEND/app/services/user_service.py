from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash

# --- Lógica de Negocio (El Cocinero) ---

def get_all_users(db: Session):
    return db.query(User).all()

def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user: UserCreate):
   # 1. Hashear la contraseña antes de guardarla
    hashed_pwd = get_password_hash(user.password)
    
    # 2. Convertir DTO a Modelo usando el hash
    new_user = User(
        email=user.email,
        nombre=user.nombre,
        password=hashed_pwd, # 👈 Guardamos el hash, NUNCA el texto plano
        activo=user.activo
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def update_user(db: Session, user_id: int, user_update: UserUpdate):
    # Reutilizamos nuestra propia función para buscar
    user_db = get_user_by_id(db, user_id)
    
    if not user_db:
        return None # Retornamos None para que el Router decida qué error lanzar

    # Actualizar campos
    if user_update.nombre is not None:
        user_db.nombre = user_update.nombre
    if user_update.email is not None:
        user_db.email = user_update.email
    if user_update.activo is not None:
        user_db.activo = user_update.activo

    db.commit()
    db.refresh(user_db)
    return user_db

def delete_user(db: Session, user_id: int):
    user_db = get_user_by_id(db, user_id)
    if user_db:
        db.delete(user_db)
        db.commit()
        return True
    return False