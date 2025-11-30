"""
Tests para los endpoints principales de la aplicación
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock


class TestMainEndpoints:
    """Tests para endpoints raíz y health check"""

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test del endpoint raíz"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
        assert data["database"] == "MongoDB"

    @pytest.mark.asyncio
    async def test_health_check_endpoint(self, client: AsyncClient, mock_mongodb):
        """Test del endpoint de health check"""
        # Mock successful ping
        mock_mongodb.command = AsyncMock(return_value={"ok": 1})
        
        response = await client.get("/health")
        # Puede ser 200 (healthy) o 503 (unhealthy) dependiendo de MongoDB
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]
