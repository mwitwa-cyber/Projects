"""Asset model for LuSE listed securities."""

from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import BaseModel, TimestampMixin


class AssetType(str, Enum):
    """Asset types on LuSE."""
    EQUITY = "equity"
    BOND = "bond"
    TREASURY_BILL = "treasury_bill"


class Sector(str, Enum):
    """LuSE sectors."""
    MINING = "mining"
    BANKING = "banking"
    ENERGY = "energy"
    RETAIL = "retail"
    MANUFACTURING = "manufacturing"
    AGRICULTURE = "agriculture"
    REAL_ESTATE = "real_estate"
    FORESTRY = "forestry"
    TELECOMMUNICATIONS = "telecommunications"
    OTHER = "other"


class Asset(BaseModel, TimestampMixin):
    """LuSE listed asset/security."""
    
    __tablename__ = "assets"
    
    # Identifiers
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    isin = Column(String(12), unique=True, nullable=True)
    name = Column(String(200), nullable=False)
    
    # Classification
    asset_type = Column(SQLEnum(AssetType), nullable=False)
    sector = Column(SQLEnum(Sector), nullable=False)
    
    # Market Data
    listed_shares = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    
    # Relationships
    price_history = relationship("PriceHistory", back_populates="asset", cascade="all, delete-orphan")
    portfolio_holdings = relationship("PortfolioHolding", back_populates="asset")
    
    def __repr__(self):
        return f"<Asset {self.ticker}: {self.name}>"
