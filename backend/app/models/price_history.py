"""Bitemporal price history model."""

from sqlalchemy import Column, Integer, Float, Date, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import BaseModel, BitemporalMixin


class PriceHistory(BaseModel, BitemporalMixin):
    """Bitemporal price history for assets.
    
    Tracks both when prices were valid and when they were recorded.
    """
    
    __tablename__ = "price_history"
    
    # Foreign Keys
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Price Data
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    
    # Trading Status
    trades_occurred = Column(Integer, default=0)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_history")
    
    __table_args__ = (
        Index('ix_price_history_temporal', 'asset_id', 'trade_date', 'valid_from', 'is_current'),
        Index('ix_price_history_transaction', 'transaction_from', 'transaction_to'),
    )
    
    def __repr__(self):
        return f"<PriceHistory {self.asset_id} {self.trade_date}: {self.close_price}>"
