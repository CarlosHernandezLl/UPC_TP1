# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base # Esto lo crearemos pronto

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    nombre = Column(String)
    password = Column(String) # En producción, ¡esto debe ir hasheado!
    role = Column(String, default="operator") # operator, admin, supervisor, auditor
    activo = Column(Boolean, default=True)