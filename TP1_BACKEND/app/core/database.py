from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# 1. Crear el motor de base de datos optimizado para GxP
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica si la conexión sigue viva antes de usarla
    pool_size=10,  # Número de conexiones constantes
    max_overflow=20,  # Conexiones extra si hay mucha carga
    connect_args={"options": "-c timezone=America/Lima"},
)

# 2. Crear la fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Clase Base para los modelos declarativos
Base = declarative_base()


# 4. Dependencia para enrutadores y servicios
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
