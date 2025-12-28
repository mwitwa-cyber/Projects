"""Portfolio and holding models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.models.base import BaseModel, TimestampMixin


class PortfolioType(str, Enum):
    """Portfolio types."""
    PERSONAL = "personal"
    INSTITUTIONAL = "institutional"
    PENSION_FUND = "pension_fund"
    INSURANCE = "insurance"


class Portfolio(BaseModel, TimestampMixin):
    """Investment portfolio."""
    
    __tablename__ = "portfolios"
    
    name = Column(String(200), nullable=False)
    description = Column(String(500), nullable=True)
    portfolio_type = Column(SQLEnum(PortfolioType), nullable=False)
    
    # Portfolio constraints
    max_single_position = Column(Float, default=0.20)
    max_sector_exposure = Column(Float, default=0.30)
    
    # Performance metrics (cached)
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    
    # Foreign Key to User
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    user = relationship("User", back_populates="portfolios")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio {self.name}>"


class PortfolioHolding(BaseModel, TimestampMixin):
    """Individual asset holding within a portfolio."""
    
    __tablename__ = "portfolio_holdings"
    
    # Foreign Keys
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Holding Data
    quantity = Column(Float, nullable=False)
    average_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    
    # Calculated fields
    total_cost = Column(Float, nullable=False)
    market_value = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    asset = relationship("Asset", back_populates="portfolio_holdings")
    
    def __repr__(self):
        return f"<Holding {self.portfolio_id}:{self.asset_id} qty={self.quantity}>"
