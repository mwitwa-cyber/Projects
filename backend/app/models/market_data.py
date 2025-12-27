"""Market-wide data and indices."""

from sqlalchemy import Column, Float, Date, String

from app.models.base import BaseModel, TimestampMixin


class MarketData(BaseModel, TimestampMixin):
    """LASI index and macroeconomic data."""
    
    __tablename__ = "market_data"
    
    observation_date = Column(Date, nullable=False, unique=True, index=True)
    
    # LASI Index
    lasi_value = Column(Float, nullable=True)
    lasi_return = Column(Float, nullable=True)
    
    # Macroeconomic
    usd_zmw_rate = Column(Float, nullable=True)
    zar_zmw_rate = Column(Float, nullable=True)
    inflation_rate = Column(Float, nullable=True)
    
    # Trading metrics
    total_volume = Column(Float, nullable=True)
    total_value_traded = Column(Float, nullable=True)
    
    def __repr__(self):
        return f"<MarketData {self.observation_date} LASI={self.lasi_value}>"
