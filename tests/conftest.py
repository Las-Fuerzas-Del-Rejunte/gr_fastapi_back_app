"""
Configuración global de pytest y fixtures
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch

# Importar la aplicación MongoDB
from main_mongodb import app as main_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_mongodb():
    """Mock MongoDB connection"""
    with patch("app.core.mongodb_connection.mongodb_client") as mock_client:
        mock_db = AsyncMock()
        mock_client.return_value = mock_db
        yield mock_db


@pytest.fixture
def mock_beanie():
    """Mock Beanie initialization"""
    with patch("app.core.mongodb_connection.init_beanie") as mock_init:
        mock_init.return_value = AsyncMock()
        yield mock_init


@pytest.fixture
async def client(mock_mongodb, mock_beanie) -> AsyncGenerator:
    """
    Async test client para la aplicación FastAPI
    """
    # Mock the lifespan to avoid MongoDB connection
    async def mock_lifespan(app: FastAPI):
        yield
    
    # Replace the lifespan
    original_lifespan = main_app.router.lifespan_context
    main_app.router.lifespan_context = mock_lifespan
    
    transport = ASGITransport(app=main_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    # Restore original lifespan
    main_app.router.lifespan_context = original_lifespan


@pytest.fixture
def mock_current_user():
    """Mock del usuario actual autenticado"""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "test@example.com",
        "nombre": "Test",
        "apellido": "User",
        "rol": "agente",
        "activo": True
    }


@pytest.fixture
def mock_auth_token():
    """Mock del token JWT"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"


@pytest.fixture
def auth_headers(mock_auth_token):
    """Headers con autenticación"""
    return {"Authorization": f"Bearer {mock_auth_token}"}
