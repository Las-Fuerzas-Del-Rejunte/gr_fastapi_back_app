"""
Excepciones personalizadas del sistema
"""


class AppException(Exception):
    """Excepción base de la aplicación"""
    def __init__(self, message: str = "Error en la aplicación"):
        self.message = message
        super().__init__(self.message)


class NotFoundException(AppException):
    """Recurso no encontrado"""
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message)


class UnauthorizedException(AppException):
    """No autorizado"""
    def __init__(self, message: str = "No autorizado"):
        super().__init__(message)


class ForbiddenException(AppException):
    """Acceso prohibido"""
    def __init__(self, message: str = "Acceso prohibido"):
        super().__init__(message)


class ValidationException(AppException):
    """Error de validación"""
    def __init__(self, message: str = "Error de validación"):
        super().__init__(message)


class DuplicateException(AppException):
    """Recurso duplicado"""
    def __init__(self, message: str = "Recurso ya existe"):
        super().__init__(message)


# Excepciones específicas por módulo

class UserNotFoundException(NotFoundException):
    """Usuario no encontrado"""
    pass


class ClaimNotFoundException(NotFoundException):
    """Reclamo no encontrado"""
    pass


class NoteNotFoundException(NotFoundException):
    """Nota no encontrada"""
    pass


class StatusNotFoundException(NotFoundException):
    """Estado no encontrado"""
    pass


class InvalidCredentialsException(UnauthorizedException):
    """Credenciales inválidas"""
    pass


class UserAlreadyExistsException(DuplicateException):
    """El usuario ya existe"""
    pass


class StatusAlreadyExistsException(DuplicateException):
    """El estado ya existe"""
    pass
