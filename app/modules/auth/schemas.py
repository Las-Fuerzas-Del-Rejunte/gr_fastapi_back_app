"""
Schemas de Autenticación - Adaptado para MongoDB
"""
from pydantic import BaseModel, EmailStr, Field, AliasChoices

from app.modules.users.schemas_mongodb import UsuarioRespuesta


# ============================================
# Request Schemas
# ============================================

class SolicitudLogin(BaseModel):
    """Schema para login"""
    email: EmailStr = Field(description="Email del usuario")
    contrasena: str = Field(
        description="Contraseña",
        validation_alias=AliasChoices('contrasena', 'password')
    )


class SolicitudRefreshToken(BaseModel):
    """Schema para renovar token"""
    refresh_token: str = Field(description="Refresh token")


class SolicitudOlvideContrasena(BaseModel):
    """Schema para solicitar recuperación de contraseña"""
    email: EmailStr = Field(description="Email del usuario")


class SolicitudRestablecerContrasena(BaseModel):
    """Schema para restablecer contraseña"""
    token: str = Field(description="Token de recuperación")
    contrasena_nueva: str = Field(
        min_length=8,
        max_length=100,
        description="Nueva contraseña"
    )


# ============================================
# Response Schemas
# ============================================

class RespuestaToken(BaseModel):
    """Schema de respuesta con tokens"""
    token: str = Field(description="Access token JWT")
    refresh_token: str = Field(description="Refresh token JWT")
    usuario: UsuarioRespuesta = Field(description="Datos del usuario")


class RespuestaMensaje(BaseModel):
    """Schema genérico para mensajes"""
    mensaje: str = Field(description="Mensaje de respuesta")
