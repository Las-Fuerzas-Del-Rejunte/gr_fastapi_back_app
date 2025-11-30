"""
Ejemplo de main.py actualizado para soportar MongoDB con Beanie
Este archivo reemplaza la configuración de SQLAlchemy por MongoDB
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Configuración
from app.core.config import Settings

# MongoDB (nuevo)
from app.core.mongodb_connection import connect_to_mongodb, close_mongodb_connection

# Routers
from app.modules.auth.routers import router as auth_router
from app.modules.users.routers import router as users_router
from app.modules.claims.routers_mongodb import router as claims_router
from app.modules.clients.routers_mongodb import (
    router_clientes as clients_router,
    router_tipos_proyecto,
    router_proyectos
)
from app.modules.status.routers_mongodb import router as status_router

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para startup y shutdown de la aplicación
    Reemplaza los eventos @app.on_event("startup") y @app.on_event("shutdown")
    """
    # ========================================
    # STARTUP - Inicialización
    # ========================================
    print("🚀 Iniciando aplicación...")
    
    # Conectar a MongoDB
    await connect_to_mongodb()
    print("✅ MongoDB conectado")
    
    # Aquí puedes agregar otras inicializaciones
    # Por ejemplo: conectar a Redis, inicializar cache, etc.
    
    yield  # La aplicación está corriendo
    
    # ========================================
    # SHUTDOWN - Limpieza
    # ========================================
    print("🛑 Cerrando aplicación...")
    
    # Cerrar conexión MongoDB
    await close_mongodb_connection()
    print("✅ MongoDB desconectado")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para Sistema de Gestión de Reclamos con MongoDB",
    lifespan=lifespan,
)

# ========================================
# Middleware CORS
# ========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios exactos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# Routers
# ========================================
app.include_router(
    auth_router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Autenticación"]
)

app.include_router(
    users_router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Usuarios"]
)

app.include_router(
    claims_router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Reclamos"]
)

app.include_router(
    clients_router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Clientes"]
)

app.include_router(
    router_tipos_proyecto,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Tipos de Proyecto"]
)

app.include_router(
    router_proyectos,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Proyectos"]
)

app.include_router(
    status_router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Estados"]
)

# ========================================
# Endpoints de Health Check
# ========================================

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Sistema de Gestión de Reclamos API",
        "version": settings.APP_VERSION,
        "database": "MongoDB",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check de la aplicación"""
    from app.core.mongodb_connection import get_database
    
    try:
        # Verificar conexión a MongoDB
        db = get_database()
        await db.command("ping")
        
        return {
            "status": "healthy",
            "database": "connected",
            "version": settings.APP_VERSION
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


# ========================================
# Ejecución directa (desarrollo)
# ========================================
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=True,  # Hot reload en desarrollo
    )
