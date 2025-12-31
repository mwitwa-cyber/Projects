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
    days: int = Query(default=1, ge=1, le=365, description="Number of days (1-365)"),
    db: Session = Depends(get_db)
):
    """
    Get OHLC candles for a ticker.
    Default: Last 24 hours (1 day).
    """
    from datetime import datetime, timedelta
    import re
    
    # Validate ticker format (alphanumeric only, max 10 chars)
    if not re.match(r'^[A-Za-z0-9]{1,10}$', ticker):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Invalid ticker format")
    
    service = MarketDataService(db)
    start_date = datetime.now() - timedelta(days=days)
    data = service.get_ohlc_data(ticker.upper(), start_date)
    return data

@router.get("/luse/latest")
def get_luse_latest():
    return {"status": "deprecated", "message": "Use /market-summary"}
