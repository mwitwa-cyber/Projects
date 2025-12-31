
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.market_data import MarketDataService
from app.services.backtest import BacktestEngine, BacktestResult

router = APIRouter()

class BacktestRequest(BaseModel):
    weights: Dict[str, float] = Field(..., description="Map of Ticker to Weight (e.g. {'ZNCO': 0.6})")
    start_date: date = Field(..., description="Start date of backtest")
    end_date: Optional[date] = Field(default_factory=date.today, description="End date")
    initial_capital: float = Field(10000.0, description="Initial investment")

@router.post("/run", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Run a historical backtest for a portfolio.
    Strategies:
    - Daily Rebalancing (Fixed Weights)
    """
    try:
        service = MarketDataService(db)
        
        # 1. Fetch Historical Data for all tickers
        # We need a method to get dataframe of closes.
        # MarketDataService currently has `get_ohlc_data`, but that returns list/dict.
        # We might need to iterate or add a batch fetch method.
        # For MVP, iterate.
        
        tickers = list(request.weights.keys())
        price_data = {}
        
        start_datetime = datetime.combine(request.start_date, datetime.min.time())
        
        for ticker in tickers:
            ohlc = service.get_ohlc_data(ticker, start_datetime)
            # ohlc is List[dict]. Convert to DF or Series
            # Structure: {time: iso, close: float, ...}
            if not ohlc:
                continue
                
            # Create dict {date: close}
            # Note: time is iso string.
            prices = {d["time"][:10]: d["close"] for d in ohlc} 
            price_data[ticker] = prices
            
        import pandas as pd
        df = pd.DataFrame(price_data)
        
        # Forward fill missing data (e.g. non-trading days differences)
        df.index = pd.to_datetime(df.index)
        df = df.sort_index().fillna(method='ffill').dropna()
        
        if df.empty:
            raise ValueError("Insufficient overlapping price data for these assets.")
            
        # 2. Run Backtest
        engine = BacktestEngine(initial_capital=request.initial_capital)
        result = engine.run_backtest(df, request.weights)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
