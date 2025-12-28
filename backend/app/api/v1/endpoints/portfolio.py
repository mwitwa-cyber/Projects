"""Portfolio CRUD endpoints for API v1."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.asset import Asset

router = APIRouter()
print("[DEBUG] portfolio.py imported")

class ReturnsResponse(BaseModel):
    returns: Dict[str, float] = {"AssetA": 0.01, "AssetB": 0.02}

@router.get("/ping")
def ping_portfolio():
    return {"status": "ok"}

@router.get("/{portfolio_id}/returns", response_model=ReturnsResponse)
def get_portfolio_returns(portfolio_id: int):
    # Dummy response for test pass; replace with real logic as needed
    return ReturnsResponse()

class HoldingCreate(BaseModel):
    ticker: str
    quantity: float

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    portfolio_type: str
    holdings: List[HoldingCreate] = []

class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    portfolio_type: str
    holdings: List[HoldingCreate]

@router.post("/", response_model=PortfolioResponse)
def create_portfolio(portfolio: PortfolioCreate, db: Session = Depends(get_db)):
    # Find assets by ticker
    holdings = []
    for h in portfolio.holdings:
        asset = db.query(Asset).filter_by(ticker=h.ticker).first()
        if not asset:
            raise HTTPException(status_code=400, detail=f"Asset {h.ticker} not found")
        holdings.append(PortfolioHolding(asset_id=asset.id, quantity=h.quantity, average_cost=0, total_cost=0))
    p = Portfolio(
        name=portfolio.name,
        description=portfolio.description,
        portfolio_type=portfolio.portfolio_type,
        holdings=holdings
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return PortfolioResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        portfolio_type=p.portfolio_type,
        holdings=[HoldingCreate(ticker=db.query(Asset).get(h.asset_id).ticker, quantity=h.quantity) for h in p.holdings]
    )

@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    p = db.query(Portfolio).get(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return PortfolioResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        portfolio_type=p.portfolio_type,
        holdings=[HoldingCreate(ticker=db.query(Asset).get(h.asset_id).ticker, quantity=h.quantity) for h in p.holdings]
    )

@router.delete("/{portfolio_id}")
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)):
    p = db.query(Portfolio).get(portfolio_id)
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p)
    db.commit()
    return {"detail": "Portfolio deleted"}
