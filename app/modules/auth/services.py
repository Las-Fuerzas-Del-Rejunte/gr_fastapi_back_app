"""
Servicios de Autenticación - Adaptado para MongoDB/Beanie
"""
from typing import Optional, Dict

from app.modules.users.models_mongodb import Usuario
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.exceptions import InvalidCredentialsException, UserNotFoundException


class AuthService:
    """Servicio para operaciones de autenticación con MongoDB"""
    
    @staticmethod
    async def login(
        email: str,
        password: str
    ) -> Dict[str, str]:
        """
        Autenticar usuario y generar tokens
        
        Args:
            email: Email del usuario
            password: Contraseña en texto plano
            
        Returns:
            Dict con access_token, refresh_token y token_type
            
        Raises:
            InvalidCredentialsException: Si las credenciales son inválidas
        """
        # Obtener usuario por email usando Beanie
        user = await Usuario.find_one(Usuario.email == email)
        
        if not user:
            raise InvalidCredentialsException("Email o contraseña incorrectos")
        
        # Verificar que el usuario esté activo
        if not user.activo:
            raise InvalidCredentialsException("Usuario inactivo")
        
        # Verificar contraseña
        if not verify_password(password, user.contrasena_hash):
            raise InvalidCredentialsException("Email o contraseña incorrectos")
        
        # Generar tokens
        return AuthService.generate_tokens(str(user.id))
    
    @staticmethod
    async def authenticate_user(
        email: str,
        password: str
    ) -> Optional[Usuario]:
        """
        Autenticar usuario con email y contraseña
        
        Returns:
            Usuario si las credenciales son válidas, None en caso contrario
        """
        user = await Usuario.find_one(Usuario.email == email)
        
        if not user or not user.activo:
            return None
        
        if not verify_password(password, user.contrasena_hash):
            return None
        
        return user
    
    @staticmethod
    def generate_tokens(user_id: str) -> Dict[str, str]:
        """
        Generar access token y refresh token
        
        Returns:
            Dict con 'access_token', 'refresh_token' y 'token_type'
        """
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def refresh_access_token(
        refresh_token: str
    ) -> Dict[str, str]:
        """
        Renovar access token usando refresh token
        
        Args:
            refresh_token: Token de refresco
            
        Returns:
            Dict con nuevo access_token y token_type
            
        Raises:
            InvalidCredentialsException: Si el refresh token es inválido
            UserNotFoundException: Si el usuario no existe
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            raise InvalidCredentialsException("Token inválido o expirado")
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            raise InvalidCredentialsException("Token inválido")
        
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidCredentialsException("Token inválido")
        
        # Verificar que el usuario existe usando Beanie
        user = await Usuario.get(user_id)
        if not user:
            raise UserNotFoundException("Usuario no encontrado")
        
        if not user.activo:
            raise InvalidCredentialsException("Usuario inactivo")
        
        # Generar nuevo access token
        access_token = create_access_token(subject=str(user.id))
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    @staticmethod
    async def verify_refresh_token(
        refresh_token: str
    ) -> Optional[Usuario]:
        """
        Verificar refresh token y obtener usuario
        
        Returns:
            Usuario si el token es válido, None en caso contrario
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            return None
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = await Usuario.get(user_id)
        if user and not user.activo:
            return None
            
        return user
