"""
Tests para los schemas de validación
"""
import pytest
from pydantic import ValidationError
from app.modules.users.schemas_mongodb import UsuarioBase, UsuarioCrear
from datetime import datetime


class TestUserSchemas:
    """Tests para schemas de usuarios"""

    def test_usuario_base_valid(self):
        """Test de creación de UsuarioBase con datos válidos"""
        data = {
            "email": "test@example.com",
            "nombre": "Test User",
            "rol": "agent",
            "activo": True
        }
        usuario = UsuarioBase(**data)
        
        assert usuario.email == "test@example.com"
        assert usuario.nombre == "Test User"
        assert usuario.rol == "agent"
        assert usuario.activo == True

    def test_usuario_base_invalid_email(self):
        """Test de validación de email inválido"""
        data = {
            "email": "invalid-email",
            "nombre": "Test",
            "apellido": "User",
            "rol": "agente"
        }
        with pytest.raises(ValidationError):
            UsuarioBase(**data)

    def test_usuario_crear_with_password(self):
        """Test de creación de usuario con contraseña"""
        data = {
            "email": "test@example.com",
            "nombre": "Test User",
            "rol": "agent",
            "contrasena": "SecurePassword123!",
            "activo": True
        }
        usuario = UsuarioCrear(**data)
        
        assert usuario.email == "test@example.com"
        assert usuario.contrasena == "SecurePassword123!"
        assert usuario.nombre == "Test User"

    def test_usuario_missing_required_fields(self):
        """Test de validación con campos requeridos faltantes"""
        data = {
            "email": "test@example.com"
            # Falta nombre, apellido, rol
        }
        with pytest.raises(ValidationError):
            UsuarioBase(**data)

    def test_usuario_rol_validation(self):
        """Test de validación de rol"""
        valid_roles = ["admin", "manager", "agent", "viewer"]
        
        for rol in valid_roles:
            data = {
                "email": "test@example.com",
                "nombre": "Test User",
                "rol": rol,
                "activo": True
            }
            usuario = UsuarioBase(**data)
            assert usuario.rol == rol
