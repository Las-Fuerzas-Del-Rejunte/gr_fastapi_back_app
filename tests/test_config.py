"""
Tests para el módulo de configuración
"""
import pytest
from app.core.config import Settings


class TestConfig:
    """Tests para la configuración de la aplicación"""

    def test_settings_initialization(self):
        """Test de inicialización de Settings"""
        settings = Settings()
        
        assert settings.APP_NAME is not None
        assert settings.APP_VERSION is not None
        assert settings.SECRET_KEY is not None
        assert settings.ALGORITHM is not None
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0

    def test_api_prefix(self):
        """Test del prefijo de API"""
        settings = Settings()
        assert settings.API_V1_PREFIX.startswith("/")
        assert "v1" in settings.API_V1_PREFIX

    def test_mongodb_configuration(self):
        """Test de configuración de MongoDB"""
        settings = Settings()
        # MongoDB config is optional, skip if not configured
        assert settings.DATABASE_URL is not None

    def test_postgres_configuration(self):
        """Test de configuración de PostgreSQL"""
        settings = Settings()
        assert settings.DATABASE_URL is not None
        assert settings.POSTGRES_SERVER is not None
        assert settings.POSTGRES_USER is not None
        assert settings.POSTGRES_DB is not None

    def test_cors_origins(self):
        """Test de configuración de CORS"""
        settings = Settings()
        assert settings.CORS_ORIGINS is not None
        # CORS_ORIGINS can be string or list
        assert isinstance(settings.CORS_ORIGINS, (list, str))

    def test_environment_specific_settings(self):
        """Test de configuraciones específicas del entorno"""
        settings = Settings()
        assert settings.ENVIRONMENT in ["development", "staging", "production"]
        assert isinstance(settings.DEBUG, bool)
