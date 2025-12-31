from sqlalchemy import Column, Integer, String, Float, DateTime, PrimaryKeyConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base
import datetime

class Security(Base):
    __tablename__ = "securities"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    name = Column(String)
    sector = Column(String)
    currency = Column(String, default="ZMW")
    
    # Bond Fields
    type = Column(String, default="Equity") # Equity, Bond
    maturity_date = Column(DateTime, nullable=True)
    coupon_rate = Column(Float, nullable=True)
    face_value = Column(Float, default=100.0)

class MarketPrice(Base):
    """
    Bitemporal Price Model.
    valid_from: The date the price actually refers to (Business Date).
    transaction_from: The time the record was inserted/known to the system (System Time).
    transaction_to: The time the record was superseded (or 'infinity' if current).
    """
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    security_ticker = Column(String, index=True)
    price = Column(Float)
    volume = Column(Integer)
    
    # Valid Time (Business Time)
    valid_from = Column(DateTime)
    
    # Transaction Time (System Time)
    transaction_from = Column(DateTime, default=func.now())
    transaction_to = Column(DateTime, nullable=True) # Null means 'Infinity' (current record)

    # Composite index for time travel queries
    __table_args__ = (
        Index('idx_bitemporal_lookup', 'security_ticker', 'valid_from', 'transaction_to'),
    )
