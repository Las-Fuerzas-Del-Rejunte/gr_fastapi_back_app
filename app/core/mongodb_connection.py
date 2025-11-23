"""
Configuración de MongoDB para FastAPI con Beanie ODM
Reemplazo de SQLAlchemy + PostgreSQL
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Cliente MongoDB global
mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    """
    Conecta a MongoDB y inicializa Beanie ODM
    Llamar en startup de FastAPI
    """
    global mongodb_client, mongodb_database
    
    # Obtener configuración desde variables de entorno
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "sistema_reclamos")
    
    # Crear cliente Motor (driver asíncrono oficial)
    mongodb_client = AsyncIOMotorClient(
        MONGODB_URL,
        maxPoolSize=10,
        minPoolSize=1,
        serverSelectionTimeoutMS=5000,
    )
    
    # Obtener base de datos
    mongodb_database = mongodb_client[MONGODB_DB_NAME]
    
    # Importar todos los modelos Document de Beanie
    from app.modules.users.models_mongodb import Usuario
    from app.modules.claims.models_mongodb import (
        Reclamo,
        ConfiguracionEstado,
        SubEstado,
        TransicionEstado,
    )
    from app.modules.clients.models_mongodb import (
        Cliente,
        TipoProyecto,
        Proyecto,
    )
    
    # Inicializar Beanie con los modelos
    await init_beanie(
        database=mongodb_database,
        document_models=[
            Usuario,
            Cliente,
            Reclamo,
            ConfiguracionEstado,
            SubEstado,
            TransicionEstado,
            TipoProyecto,
            Proyecto,
        ]
    )
    
    print("✅ Conectado a MongoDB exitosamente")


async def close_mongodb_connection():
    """
    Cierra la conexión a MongoDB
    Llamar en shutdown de FastAPI
    """
    global mongodb_client
    
    if mongodb_client:
        mongodb_client.close()
        print("✅ Conexión a MongoDB cerrada")


def get_database() -> AsyncIOMotorDatabase:
    """
    Obtiene la instancia de la base de datos MongoDB
    Usar para operaciones que no son con Beanie
    """
    if mongodb_database is None:
        raise Exception("MongoDB no está conectado")
    return mongodb_database


# Dependency para FastAPI (si necesitas acceso directo a la DB)
async def get_mongodb() -> AsyncIOMotorDatabase:
    """
    Dependency de FastAPI para inyectar MongoDB
    
    Uso:
        @router.get("/")
        async def endpoint(db: AsyncIOMotorDatabase = Depends(get_mongodb)):
            pass
    """
    return get_database()
