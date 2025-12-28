"""Base model with common fields and bitemporal support."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.sql import func

from app.core.database import Base, get_db


class BitemporalMixin:
    """Mixin for bitemporal data modeling.
    
    Implements two time dimensions:
    - Valid Time (VT): When the fact is true in the real world
    - Transaction Time (TT): When the fact was recorded in the system
    """
    
    # Valid Time dimension
    valid_from = Column(DateTime, nullable=False, index=True)
    valid_to = Column(DateTime, nullable=True, index=True)
    
    # Transaction Time dimension
    transaction_from = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    transaction_to = Column(DateTime, nullable=True, index=True)
    
    # Helper flag for current version
    is_current = Column(Boolean, default=True, index=True)
    
    def close_transaction(self, close_time: datetime = None):
        """Close the transaction time for this record."""
        self.transaction_to = close_time or datetime.utcnow()
        self.is_current = False


class TimestampMixin:
    """Mixin for created/updated timestamps."""
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class BaseModel(Base):
    """Base model class with common fields."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
