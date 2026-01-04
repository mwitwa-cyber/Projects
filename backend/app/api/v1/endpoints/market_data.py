from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import get_db
from app.services.market_data import MarketDataService
from pydantic import BaseModel
from fastapi_cache.decorator import cache

router = APIRouter()

class PricePoint(BaseModel):
    date: str
    value: float

class MarketSummaryItem(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    price: Optional[float] = None
    change: float = 0.0
    change_percent: float = 0.0
    history: List[PricePoint] = []

class SecurityResponse(BaseModel):
    ticker: str
    name: str
    sector: str

class ExchangeRateResponse(BaseModel):
    base: str
    target: str
    rate: float
    source: str
    timestamp: str

@router.get("/exchange-rate", response_model=ExchangeRateResponse)
@cache(expire=3600)  # Cache for 1 hour
def get_exchange_rate():
    """
    Get current USD/ZMW exchange rate.
    Sources (in order of priority):
    1. Bank of Zambia official rate
    2. ExchangeRate-API
    3. Frankfurter API
    4. Environment variable fallback
    """
    from datetime import datetime
    from app.services.currency import get_usd_zmw_rate, _rate_cache
    
    rate = get_usd_zmw_rate()
    
    # Determine source
    source = "default"
    if _rate_cache.get("timestamp"):
        source = "cached (BoZ/API)"
    
    return {
        "base": "USD",
        "target": "ZMW",
        "rate": rate,
        "source": source,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/market-summary", response_model=List[MarketSummaryItem])
@cache(expire=60)
def get_market_summary(
    date_str: Optional[str] = Query(None, alias="date"),
    db: Session = Depends(get_db)
):
    """
    Get market summary for a specific date (default: today).
    Includes price, change, and 30-day sparkline history.
    """
    service = MarketDataService(db)
    target_date = date.today()
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            pass # Fallback to today
            
    summary = service.get_market_summary(target_date)
    return summary

@router.get("/securities", response_model=List[SecurityResponse])
@cache(expire=300)
def get_securities(db: Session = Depends(get_db)):
    """Get list of all securities."""
    # Quick ad-hoc query since service doesn't have a direct method for just this, 
    # or we can extract from summary.
    # Better to query Security model directly or add method to service.
    # For now, using service internal session or replicating valid logic.
    from app.core.models import Security
    securities = db.query(Security).all()
    return [{"ticker": s.ticker, "name": s.name, "sector": s.sector} for s in securities]

@router.get("/ohlc/{ticker}")
@cache(expire=60)
def get_ohlc_data(
    ticker: str,
    days: int = Query(default=1, ge=1, le=1825, description="Number of days (1-1825, ~5 years)"),
    db: Session = Depends(get_db)
):
    """
    Get OHLC candles for a ticker.
    Default: Last 24 hours (1 day).
    """
    from datetime import datetime, timedelta
    import re
    
    # Validate ticker format (alphanumeric and hyphens, max 15 chars)
    if not re.match(r'^[A-Za-z0-9-]{1,15}$', ticker):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid ticker format")
    
    service = MarketDataService(db)
    start_date = datetime.now() - timedelta(days=days)
    data = service.get_ohlc_data(ticker.upper(), start_date)
    return data

@router.get("/returns/{ticker}")
@cache(expire=300)
def get_security_returns(
    ticker: str,
    periods: int = Query(default=52, ge=4, le=260, description="Number of weekly periods (4-260)"),
    db: Session = Depends(get_db)
):
    """
    Get historical weekly returns for a security.
    
    Returns log returns calculated from weekly closing prices.
    Default: 52 weeks (1 year).
    
    This is used by the Portfolio Optimizer to auto-populate asset returns.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import text
    import numpy as np
    import re
    from fastapi import HTTPException
    
    # Validate ticker format
    if not re.match(r'^[A-Za-z0-9-]{1,15}$', ticker):
        raise HTTPException(status_code=400, detail="Invalid ticker format")
    
    ticker = ticker.upper()
    
    # Get weekly closing prices using our bitemporal model
    # We need at least periods+1 data points to calculate 'periods' returns
    days_needed = (periods + 5) * 7  # Add buffer
    start_date = datetime.now() - timedelta(days=days_needed)
    
    # Query prices grouped by week
    result = db.execute(text("""
        WITH weekly_prices AS (
            SELECT 
                DATE_TRUNC('week', valid_from) as week_start,
                MAX(price) as close_price
            FROM market_prices 
            WHERE security_ticker = :ticker 
              AND valid_from >= :start_date
              AND transaction_to IS NULL
            GROUP BY DATE_TRUNC('week', valid_from)
            ORDER BY week_start
        )
        SELECT week_start, close_price FROM weekly_prices
        ORDER BY week_start
    """), {"ticker": ticker, "start_date": start_date})
    
    rows = result.fetchall()
    
    if len(rows) < 2:
        return {
            "ticker": ticker,
            "returns": [],
            "periods": 0,
            "message": "Insufficient price history for returns calculation"
        }
    
    # Calculate log returns
    prices = [row[1] for row in rows]
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] > 0 and prices[i] > 0:
            log_return = np.log(prices[i] / prices[i-1])
            returns.append(round(float(log_return), 6))
    
    # Limit to requested periods
    returns = returns[-periods:] if len(returns) > periods else returns
    
    return {
        "ticker": ticker,
        "returns": returns,
        "periods": len(returns),
        "mean_return": round(float(np.mean(returns)), 6) if returns else 0,
        "volatility": round(float(np.std(returns)), 6) if returns else 0,
        "start_date": rows[0][0].isoformat() if rows else None,
        "end_date": rows[-1][0].isoformat() if rows else None
    }


@router.post("/bulk-returns")
@cache(expire=300)
def get_bulk_returns(
    tickers: List[str],
    periods: int = Query(default=52, ge=4, le=260),
    db: Session = Depends(get_db)
):
    """
    Get historical weekly returns for multiple securities at once.
    Used by Portfolio Optimizer for efficient data loading.
    """
    results = {}
    for ticker in tickers[:20]:  # Limit to 20 assets
        result = get_security_returns(ticker, periods, db)
        if result["returns"]:
            results[ticker.upper()] = result
    return results


@router.get("/luse/latest")
def get_luse_latest():
    return {"status": "deprecated", "message": "Use /market-summary"}
