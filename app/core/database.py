from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from urllib.parse import quote_plus
import os

load_dotenv()

# Obtener DATABASE_URL directamente (ya está configurada en .env)
DATABASE_URL = os.getenv("DATABASE_URL")

# Si no existe DATABASE_URL, construirla desde variables individuales
if not DATABASE_URL:
    USER = os.getenv("POSTGRES_USER") or os.getenv("user")
    PASSWORD = os.getenv("POSTGRES_PASSWORD") or os.getenv("password")
    HOST = os.getenv("POSTGRES_SERVER") or os.getenv("host")
    PORT = os.getenv("POSTGRES_PORT") or os.getenv("port", "5432")
    DBNAME = os.getenv("POSTGRES_DB") or os.getenv("dbname", "postgres")
    
    if PASSWORD:
        DATABASE_URL = f"postgresql+asyncpg://{USER}:{quote_plus(PASSWORD)}@{HOST}:{PORT}/{DBNAME}"
    else:
        raise ValueError("No se pudo construir DATABASE_URL: falta PASSWORD o DATABASE_URL en .env")

# Crear engine asíncrono
engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Supabase Session Pooler ya maneja pooling
    echo=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()