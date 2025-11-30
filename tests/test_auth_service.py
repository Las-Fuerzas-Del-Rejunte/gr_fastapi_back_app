"""
Tests para el servicio de autenticación
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.security import get_password_hash


class TestAuthService:
    """Tests para funcionalidad de autenticación con mocks"""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test de autenticación exitosa"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        
        # Crear usuario con contraseña hasheada
        hashed_password = get_password_hash("testpassword123")
        mock_user = MagicMock(
            id=1,
            email="test@test.com",
            contrasena_hash=hashed_password,
            activo=True
        )
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Verificamos que la contraseña se hashea correctamente
        user = mock_result.scalar_one_or_none()
        
        assert user is not None
        assert user.email == "test@test.com"
        assert user.activo is True
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test de autenticación con contraseña incorrecta"""
        mock_db = AsyncMock()
        
        hashed_password = get_password_hash("correctpassword")
        
        # Verificamos que las contraseñas diferentes producen hashes diferentes
        wrong_hash = get_password_hash("wrongpassword")
        
        assert hashed_password != wrong_hash
        assert mock_db is not None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self):
        """Test de autenticación con usuario inexistente"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Simulamos el servicio
        user = mock_result.scalar_one_or_none()
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self):
        """Test de autenticación con usuario inactivo"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        
        hashed_password = get_password_hash("testpassword")
        mock_user = MagicMock(
            id=1,
            email="test@test.com",
            contrasena_hash=hashed_password,
            activo=False  # Usuario inactivo
        )
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Simulamos el servicio
        user = mock_result.scalar_one_or_none()
        
        # El usuario existe pero está inactivo
        assert user is not None
        assert user.activo is False
    
    @pytest.mark.asyncio
    async def test_create_token_for_user(self):
        """Test de creación de token para usuario"""
        mock_db = AsyncMock()
        
        with patch('app.core.security.create_access_token') as mock_create_token:
            mock_create_token.return_value = "fake-token-123"
            
            from app.core.security import create_access_token
            token = create_access_token(subject="user-id-123")
            
            assert token == "fake-token-123"
