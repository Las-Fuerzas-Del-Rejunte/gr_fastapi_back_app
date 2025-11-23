"""
Sistema de Gestión de Reclamos - Main Application
FastAPI Backend API con MongoDB
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings

# MongoDB (nuevo) - Reemplaza SQLAlchemy
from app.core.mongodb_connection import connect_to_mongodb, close_mongodb_connection, get_database

# Importar routers
from app.modules.auth.routers import router as auth_router
from app.modules.users.routers import router as usuarios_router
from app.modules.claims.routers_mongodb import router as reclamos_router
from app.modules.status.routers_mongodb import router as estados_router
from app.modules.clients.routers_mongodb import (
    router_clientes,
    router_tipos_proyecto,
    router_proyectos
)


# ============================================
# Lifespan - Event Handlers (nuevo estilo FastAPI)
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager para startup y shutdown de la aplicación
    Reemplaza @app.on_event("startup") y @app.on_event("shutdown")
    """
    # STARTUP
    print(f">> Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f">> API Documentation: http://localhost:8000/docs")
    
    # Conectar a MongoDB
    await connect_to_mongodb()
    print(f">> Connected to MongoDB")
    print(f">> Application ready!")
    
    yield  # La aplicación está corriendo
    
    # SHUTDOWN
    print(">> Shutting down application...")
    await close_mongodb_connection()
    print(">> MongoDB disconnected")


# ============================================
# Crear aplicación FastAPI
# ============================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API REST para gestión de reclamos con MongoDB",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,  # Nuevo: agregar lifespan
)


# ============================================
# Configurar CORS
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Incluir Routers
# ============================================

# Router principal con prefijo API v1
api_prefix = settings.API_V1_PREFIX

# Auth router (ya adaptado a MongoDB)
app.include_router(auth_router, prefix=api_prefix)

# Users router (ya adaptado a MongoDB)
app.include_router(usuarios_router, prefix=api_prefix)

# Claims/Reclamos router (ya adaptado a MongoDB)
app.include_router(reclamos_router, prefix=api_prefix)

# Status/Estados router (ya adaptado a MongoDB)
app.include_router(estados_router, prefix=api_prefix)

# Clients routers (ya adaptado a MongoDB)
app.include_router(router_clientes, prefix=api_prefix)
app.include_router(router_tipos_proyecto, prefix=api_prefix)
app.include_router(router_proyectos, prefix=api_prefix)


# ============================================
# Endpoints raíz
# ============================================

@app.get("/")
async def root():
    """Endpoint raíz - Información de la API"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verificar conexión a MongoDB
        db = get_database()
        await db.command("ping")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "database": "MongoDB - Connected ✅",
                "version": settings.APP_VERSION
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "MongoDB - Disconnected ❌",
                "error": str(e)
            }
        )


# ============================================
# Exception Handlers
# ============================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handler para recursos no encontrados"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Recurso no encontrado"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler para errores internos del servidor"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"}
    )