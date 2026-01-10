"""Simplified price service.

Replaces the complex BitemporalService with a lightweight CRUD service.
Advanced bitemporal features (valid_time, transaction_time) are currently stubbed/minimized.
"""

from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.price_history import PriceHistory


class SimplePriceService:
    """Lightweight price service."""
    
    def __init__(self, db: Session):
        self.db = db

    def get_price(self, asset_id: int, trade_date: date) -> Optional[PriceHistory]:
        """Get price for asset on date."""
        return self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date == trade_date
        ).first()
    
    def insert_price(self, asset_id: int, trade_date: date, close_price: float, volume: int = 0):
        """Insert new price."""
        # Ensure we populate required bitemporal fields even if we don't use the features yet
        price = PriceHistory(
            asset_id=asset_id,
            trade_date=trade_date,
            close_price=close_price,
            volume=volume
        )
        self.db.add(price)
        self.db.commit()
        return price
    
    def get_price_history(self, asset_id: int, start_date: date, end_date: date) -> List[PriceHistory]:
        """Get price range."""
        return self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date >= start_date,
            PriceHistory.trade_date <= end_date
        ).order_by(PriceHistory.trade_date).all()
