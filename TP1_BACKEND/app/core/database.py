from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 1. Crear el motor
engine = create_engine(settings.DATABASE_URL)

# 2. Crear la sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base para los modelos
Base = declarative_base()

# 4. Dependencia get_db
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()