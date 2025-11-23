"""
Modelo de Nota de Reclamo (ClaimNote)
"""
from sqlalchemy import Column, Text, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.models import BaseModel


class ClaimNote(BaseModel):
    """
    Modelo de Nota/Comentario de Reclamo
    
    Tabla: notas_reclamo
    """
    __tablename__ = "notas_reclamo"
    
    contenido = Column(Text, nullable=False)
    autor = Column(String(255), nullable=False)
    
    # Foreign Keys
    reclamo_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reclamos.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Relaciones
    reclamo = relationship("Claim", back_populates="notas")
    
    def __repr__(self):
        return f"<ClaimNote by {self.autor} on Claim {self.reclamo_id}>"
