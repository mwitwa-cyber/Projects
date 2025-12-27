from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.services.market_data import MarketDataService
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

router = APIRouter()

class PriceIngest(BaseModel):
    ticker: str
    price: float
    volume: int
    date: date

class TickerCreate(BaseModel):
    ticker: str
    name: str
    sector: str

@router.post("/tickers")
def create_ticker(ticker: TickerCreate, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    return service.create_ticker(ticker.ticker, ticker.name, ticker.sector)

@router.post("/prices")
def ingest_price(data: PriceIngest, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    return service.ingest_price(data.ticker, data.price, data.volume, data.date)

@router.get("/prices/{ticker}")
def get_price(ticker: str, date: date, as_of: Optional[datetime] = None, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    result = service.get_price_as_of(ticker, date, as_of)
    if not result:
        raise HTTPException(status_code=404, detail="Price not found")
    return {"ticker": result.security_ticker, "price": result.price, "valid_date": result.valid_from, "knowledge_time": as_of or "now"}

@router.get("/securities")
def get_securities(db: Session = Depends(get_db)):
    service = MarketDataService(db)
    # create a method in service or just query directly if service doesn't have it yet. 
    # Checking service first is better but I don't see the service file content yet so I will implement it in the service or just do it here if service is simple.
    # Let's check service content first? No, let's just use the db directly here for simplicity or add to service.
    # Wait, I should check `MarketDataService` content first to be clean.
    # But I can just add the method to the service in the same step if I knew the file. 
    # I'll optimistically assume I can just query `Security` model directly here for now or add it to service.
    # Let's query model directly to be safe as I haven't seen service file.
    from app.core.models import Security
    return db.query(Security).all()

@router.get("/market-summary")
def get_market_summary(date: date, db: Session = Depends(get_db)):
    service = MarketDataService(db)
    return service.get_market_summary(date)
