"""Bitemporal data service for temporal queries and data versioning.

This service provides methods to query and manage bitemporal data,
allowing for:
- Point-in-time queries (as of valid time)
- Historical state queries (as of transaction time)
- Data corrections and versioning
- Audit trail management
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory
from app.models.asset import Asset


class BitemporalService:
    """Service for managing bitemporal data operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Query Methods ====================
    
    def get_current_price(self, asset_id: int, trade_date: date) -> Optional[PriceHistory]:
        """Get the current version of price data for a specific date.
        
        This returns what we currently believe the price was on the given date.
        
        Args:
            asset_id: Asset identifier
            trade_date: The date for which to get the price
            
        Returns:
            Current price record or None
        """
        return self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date == trade_date,
            PriceHistory.is_current == True
        ).first()
    
    def get_price_as_of_valid_time(
        self,
        asset_id: int,
        trade_date: date,
        as_of: datetime
    ) -> Optional[PriceHistory]:
        """Get price data as it was valid at a specific point in time.
        
        This answers: "What was the price on trade_date, considering only
        data that was valid as of the 'as_of' timestamp?"
        
        Args:
            asset_id: Asset identifier
            trade_date: The trade date
            as_of: The valid time cutoff
            
        Returns:
            Price record valid at the specified time
        """
        return self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date == trade_date,
            PriceHistory.valid_from <= as_of,
            or_(
                PriceHistory.valid_to == None,
                PriceHistory.valid_to > as_of
            )
        ).first()
    
    def get_price_as_of_transaction_time(
        self,
        asset_id: int,
        trade_date: date,
        as_of: datetime
    ) -> Optional[PriceHistory]:
        """Get price data as it was recorded in the system at a specific time.
        
        This answers: "What did we THINK the price was on trade_date,
        based on what was in the database at the 'as_of' timestamp?"
        
        This is critical for backtesting to avoid look-ahead bias.
        
        Args:
            asset_id: Asset identifier
            trade_date: The trade date
            as_of: The transaction time cutoff
            
        Returns:
            Price record as recorded in system at specified time
        """
        return self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date == trade_date,
            PriceHistory.transaction_from <= as_of,
            or_(
                PriceHistory.transaction_to == None,
                PriceHistory.transaction_to > as_of
            )
        ).first()
    
    def get_price_history_range(
        self,
        asset_id: int,
        start_date: date,
        end_date: date,
        as_of_transaction: Optional[datetime] = None
    ) -> List[PriceHistory]:
        """Get price history for a date range.
        
        Args:
            asset_id: Asset identifier
            start_date: Start of date range
            end_date: End of date range
            as_of_transaction: Optional transaction time for historical view
            
        Returns:
            List of price records in the date range
        """
        query = self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date >= start_date,
            PriceHistory.trade_date <= end_date
        )
        
        if as_of_transaction:
            # Historical view: what did we know at this time?
            query = query.filter(
                PriceHistory.transaction_from <= as_of_transaction,
                or_(
                    PriceHistory.transaction_to == None,
                    PriceHistory.transaction_to > as_of_transaction
                )
            )
        else:
            # Current view
            query = query.filter(PriceHistory.is_current == True)
        
        return query.order_by(PriceHistory.trade_date).all()
    
    def correct_price(
        self,
        asset_id: int,
        trade_date: date,
        corrected_close_price: float,
        corrected_open_price: Optional[float] = None,
        corrected_high_price: Optional[float] = None,
        corrected_low_price: Optional[float] = None,
        corrected_volume: Optional[float] = None,
        correction_reason: Optional[str] = None
    ) -> PriceHistory:
        """Correct an existing price record while preserving history."""
        current_record = self.get_current_price(asset_id, trade_date)
        
        if not current_record:
            raise ValueError(
                f"No current price record found for asset {asset_id} "
                f"on {trade_date}"
            )
        
        now = datetime.utcnow()
        
        # Close the old record's transaction time
        current_record.close_transaction(now)
        
        # Create corrected record with same valid time but new transaction time
        corrected_record = PriceHistory(
            asset_id=asset_id,
            trade_date=trade_date,
            close_price=corrected_close_price,
            open_price=corrected_open_price or current_record.open_price,
            high_price=corrected_high_price or current_record.high_price,
            low_price=corrected_low_price or current_record.low_price,
            volume=corrected_volume or current_record.volume,
            trades_occurred=current_record.trades_occurred,
            valid_from=current_record.valid_from,
            valid_to=current_record.valid_to,
            transaction_from=now,
            transaction_to=None,
            is_current=True
        )
        
        self.db.add(corrected_record)
        self.db.commit()
        self.db.refresh(corrected_record)
        
        return corrected_record
