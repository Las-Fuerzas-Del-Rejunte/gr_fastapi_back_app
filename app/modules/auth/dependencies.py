"""
Dependencies de Autenticación - Adaptado para MongoDB/Beanie
"""
from typing import Callable, Literal
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_token
from app.modules.users.models_mongodb import Usuario

# Security scheme para JWT Bearer
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Usuario:
    """
    Dependency para obtener el usuario actual desde el token JWT
    
    Raises:
        HTTPException: Si el token es inválido o el usuario no existe
    
    Returns:
        Usuario actual autenticado
    """
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Obtener usuario usando Beanie
    try:
        user = await Usuario.get(ObjectId(user_id))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_role(*allowed_roles: Literal["admin", "manager", "agent", "viewer"]) -> Callable:
    """
    Dependency factory para requerir roles específicos
    
    Args:
        *allowed_roles: Roles permitidos ("admin", "manager", "agent", "viewer")
    
    Returns:
        Dependency function
    
    Example:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user = Depends(require_role("admin"))
        ):
            ...
    """
    async def role_checker(
        current_user: Usuario = Depends(get_current_user)
    ) -> Usuario:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos suficientes"
            )
        return current_user
    
    return role_checker


# Aliases útiles
require_admin = require_role("admin")
require_manager = require_role("manager", "admin")
require_agent = require_role("agent", "manager", "admin")
