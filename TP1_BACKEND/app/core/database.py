from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

print(repr(settings.DATABASE_URL))

# 1. Crear el motor
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica si la conexión sigue viva antes de usarla
    pool_size=10,        # Número de conexiones constantes
    max_overflow=20,     # Conexiones extra si hay mucha carga
    connect_args={"options": "-c timezone=America/Lima"}
)

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