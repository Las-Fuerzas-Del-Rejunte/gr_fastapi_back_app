"""
Configuración centralizada de la aplicación
Similar a settings.py de Django
"""
from typing import List, Optional
from pydantic import PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración principal de la aplicación
    Las variables se pueden sobrescribir con archivo .env
    """
    
    # ============================================
    # Configuración General
    # ============================================
    APP_NAME: str = "Sistema de Gestión de Reclamos"
    APP_VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    
    # ============================================
    # Base de Datos PostgreSQL
    # ============================================
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "sistema_reclamos"
    
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> str:
        """Construye la URL de conexión a la base de datos"""
        if isinstance(v, str):
            return v
        
        data = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_SERVER"),
            port=data.get("POSTGRES_PORT"),
            path=f"{data.get('POSTGRES_DB') or ''}",
        ).unicode_string()
    
    # Pool de conexiones (para producción)
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # ============================================
    # JWT y Seguridad
    # ============================================
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ============================================
    # Supabase (Storage, Auth, Realtime)
    # ============================================
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWT_SECRET: Optional[str] = None
    
    # Storage para archivos adjuntos
    SUPABASE_STORAGE_BUCKET: str = "adjuntos-reclamos"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "pdf,doc,docx,jpg,jpeg,png,gif,txt,xlsx,xls,zip"
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convierte ALLOWED_FILE_TYPES a lista"""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(",")]
    
    # ============================================
    # CORS
    # ============================================
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080"
    
    @property
    def backend_cors_origins(self) -> List[str]:
        """Parsea CORS_ORIGINS a lista"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    # ============================================
    # Paginación
    # ============================================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ============================================
    # Passwords
    # ============================================
    PWD_CONTEXT_SCHEMES: List[str] = ["bcrypt"]
    PWD_CONTEXT_DEPRECATED: str = "auto"
    
    # ============================================
    # Logging
    # ============================================
    LOG_LEVEL: str = "INFO"
    SQL_ECHO: bool = False
    
    # ============================================
    # Rate Limiting (opcional)
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # ============================================
    # Email (para futuras implementaciones)
    # ============================================
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # ============================================
    # Configuración de Pydantic Settings
    # ============================================
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Instancia global de configuración
settings = Settings()
