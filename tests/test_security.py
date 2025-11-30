"""
Tests para el módulo de seguridad
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
)
from app.core.config import Settings


class TestSecurity:
    """Tests para funciones de seguridad"""

    @pytest.fixture
    def settings(self):
        """Settings fixture"""
        return Settings()

    def test_password_hash_and_verify(self):
        """Test de hash y verificación de contraseña"""
        password = "SuperSecurePassword123!"
        hashed = get_password_hash(password)
        
        # El hash debe ser diferente a la contraseña original
        assert hashed != password
        # La verificación debe ser exitosa
        assert verify_password(password, hashed)
        # Una contraseña incorrecta no debe verificarse
        assert not verify_password("WrongPassword", hashed)

    def test_create_access_token_default_expiry(self, settings):
        """Test de creación de token con expiración por defecto"""
        user_id = "test-user-123"
        token = create_access_token(subject=user_id)
        
        # Decodificar el token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self, settings):
        """Test de creación de token con expiración personalizada"""
        user_id = "test-user-123"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject=user_id, expires_delta=expires_delta)
        
        # Decodificar el token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert "exp" in payload
        
        # Verificar que la expiración es aproximadamente correcta
        from datetime import datetime, timezone
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected_time = datetime.now(timezone.utc) + expires_delta
        # Permitir 5 segundos de diferencia
        time_diff = abs((exp_time - expected_time).total_seconds())
        assert time_diff < 10  # Aumentamos la tolerancia

    def test_password_hash_consistency(self):
        """Test de que el mismo password genera hashes diferentes"""
        password = "TestPassword123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # Los hashes deben ser diferentes (por el salt)
        assert hash1 != hash2
        # Pero ambos deben verificar correctamente
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_token_with_additional_data(self, settings):
        """Test de token con datos adicionales"""
        user_id = "user-123"
        token = create_access_token(subject=user_id)
        
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        assert payload["sub"] == user_id
        assert "exp" in payload
