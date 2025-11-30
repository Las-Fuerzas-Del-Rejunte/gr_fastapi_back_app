"""
Tests para excepciones personalizadas
"""
import pytest
from app.core.exceptions import (
    ClaimNotFoundException,
    UserNotFoundException,
    NoteNotFoundException,
    DuplicateException
)


class TestCustomExceptions:
    """Tests para excepciones personalizadas"""

    def test_claim_not_found_exception(self):
        """Test de ClaimNotFoundException"""
        claim_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with pytest.raises(ClaimNotFoundException) as exc_info:
            raise ClaimNotFoundException(claim_id)
        
        assert str(claim_id) in str(exc_info.value)

    def test_user_not_found_exception(self):
        """Test de UserNotFoundException"""
        user_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with pytest.raises(UserNotFoundException) as exc_info:
            raise UserNotFoundException(user_id)
        
        assert str(user_id) in str(exc_info.value)

    def test_note_not_found_exception(self):
        """Test de NoteNotFoundException"""
        note_id = "550e8400-e29b-41d4-a716-446655440000"
        
        with pytest.raises(NoteNotFoundException) as exc_info:
            raise NoteNotFoundException(note_id)
        
        assert str(note_id) in str(exc_info.value)

    def test_duplicate_exception(self):
        """Test de DuplicateException"""
        message = "El registro ya existe"
        
        with pytest.raises(DuplicateException) as exc_info:
            raise DuplicateException(message)
        
        assert message in str(exc_info.value)

    def test_exception_inheritance(self):
        """Test de herencia de excepciones"""
        assert issubclass(ClaimNotFoundException, Exception)
        assert issubclass(UserNotFoundException, Exception)
        assert issubclass(NoteNotFoundException, Exception)
        assert issubclass(DuplicateException, Exception)
