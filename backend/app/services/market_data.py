from app.core.models import MarketPrice, Security
from datetime import datetime, date, timedelta

from sqlalchemy.orm import Session

class MarketDataService:
    def __init__(self, db: Session):
        self.db = db

    def create_ticker(self, ticker: str, name: str, sector: str, 
                      security_type: str = "Equity", 
                      maturity_date: datetime = None, 
                      coupon_rate: float = None):
        sec = Security(
            ticker=ticker, 
            name=name, 
            sector=sector,
            type=security_type,
            maturity_date=maturity_date,
            coupon_rate=coupon_rate
        )
        self.db.add(sec)
        self.db.commit()
        return sec

    def ingest_price(self, ticker: str, price: float, volume: int, valid_date: date):
        """
        Ingests a new price. If a correction, it closes the old transaction interval.
        Note: logic simplified for prototype. A full implementation would checking for existing overlap.
        """
        # Close previous record for this valid_date if exists (Correction scenario)
        existing = self.db.query(MarketPrice).filter(
            MarketPrice.security_ticker == ticker,
            MarketPrice.valid_from == valid_date,
            MarketPrice.transaction_to == None
        ).first()

        if existing:
            existing.transaction_to = datetime.now()
            self.db.add(existing)
        
        # Insert new record
        new_price = MarketPrice(
            security_ticker=ticker,
            price=price,
            volume=volume,
            valid_from=valid_date,
            transaction_from=datetime.now(),
            transaction_to=None 
        )
        self.db.add(new_price)
        self.db.commit()
        return new_price

    def get_price_as_of(self, ticker: str, valid_date: date, as_of_time: datetime = None):
        """
        Time Travel Query: What did we think the price was at `as_of_time`?
        """
        query = self.db.query(MarketPrice).filter(
            MarketPrice.security_ticker == ticker,
            MarketPrice.valid_from == valid_date,
            MarketPrice.transaction_from <= (as_of_time or datetime.now())
        )

        if as_of_time:
             query = query.filter(
                 (MarketPrice.transaction_to == None) | (MarketPrice.transaction_to > as_of_time)
             )
        else:
             query = query.filter(MarketPrice.transaction_to == None)
             
        return query.first()

    def get_market_summary(self, valid_date: date):
        """
        Returns a summary of all securities with their latest price, percentage change,
        and a 30-day price history for sparklines.
        """
        securities = self.db.query(Security).all()
        summary = []
        
        # Date range for history (last 30 days)
        start_date = valid_date - timedelta(days=30)
        
        for sec in securities:
            # Current Price
            current_price_record = self.get_price_as_of(sec.ticker, valid_date)
            current_price = current_price_record.price if current_price_record else None
            
            # Previous Price (Yesterday)
            prev_date = valid_date - timedelta(days=1)
            prev_price_record = self.get_price_as_of(sec.ticker, prev_date)
            prev_price = prev_price_record.price if prev_price_record else None
            
            # Change Calculation
            change = 0.0
            change_percent = 0.0
            
            if current_price and prev_price:
                change = current_price - prev_price
                if prev_price != 0:
                    change_percent = (change / prev_price) * 100
            
            # History for Sparkline
            # Fetch all valid prices for this ticker between start_date and valid_date
            # Note regarding bitemporality: We want the "latest known" price for each valid_date in the range.
            # For simplicity in this view, we'll query MarketPrice directly filtering by valid_from range 
            # and taking the latest transaction for each valid_from.
            # Or simpler: just get the active records (transaction_to is NULL).
            
            history_query = self.db.query(MarketPrice.valid_from, MarketPrice.price).filter(
                MarketPrice.security_ticker == sec.ticker,
                MarketPrice.valid_from >= start_date,
                MarketPrice.valid_from <= valid_date,
                MarketPrice.transaction_to == None
            ).order_by(MarketPrice.valid_from).all()
            
            history = [{"date": h.valid_from.strftime("%Y-%m-%d"), "value": h.price} for h in history_query]

            summary.append({
                "ticker": sec.ticker,
                "name": sec.name,
                "sector": sec.sector,
                "price": current_price,
                "change": round(change, 4),
                "change_percent": round(change_percent, 2),
                "history": history
            })
            
        return summary

    def get_ohlc_data(self, ticker: str, start_date: datetime) -> list[dict]:
        """
        Queries OHLC data for a ticker. Falls back to market_prices if ohlc_1min doesn't exist.
        """
        from sqlalchemy import text
        from sqlalchemy.exc import ProgrammingError
        
        # Try the ohlc_1min continuous aggregate first
        try:
            query = text("""
                SELECT bucket, open, high, low, close, volume
                FROM ohlc_1min
                WHERE security_ticker = :ticker
                AND bucket >= :start_date
                ORDER BY bucket ASC
            """)
            
            result = self.db.execute(query, {"ticker": ticker, "start_date": start_date})
            
            data = []
            for row in result:
                data.append({
                    "time": row.bucket.isoformat(),
                    "open": row.open,
                    "high": row.high,
                    "low": row.low,
                    "close": row.close,
                    "volume": row.volume
                })
                
            return data
        except ProgrammingError:
            # ohlc_1min table doesn't exist, fall back to market_prices
            self.db.rollback()
            pass
        
        # Fallback: Use market_prices table (daily prices)
        # Construct OHLC-like data from daily prices
        prices = self.db.query(MarketPrice).filter(
            MarketPrice.security_ticker == ticker,
            MarketPrice.valid_from >= start_date.date() if isinstance(start_date, datetime) else start_date,
            MarketPrice.transaction_to == None
        ).order_by(MarketPrice.valid_from.asc()).all()
        
        data = []
        for price in prices:
            # For daily data, open/high/low/close are the same
            data.append({
                "time": price.valid_from.strftime("%Y-%m-%d") if hasattr(price.valid_from, 'strftime') else str(price.valid_from),
                "open": price.price,
                "high": price.price,
                "low": price.price,
                "close": price.price,
                "volume": price.volume or 0
            })
            
        return data
