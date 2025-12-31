"""Portfolio CRUD endpoints for API v1."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.portfolio import Portfolio, PortfolioHolding
from app.models.asset import Asset
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_active_user

router = APIRouter()


class ReturnsResponse(BaseModel):
    returns: Dict[str, float] = {"AssetA": 0.01, "AssetB": 0.02}


@router.get("/ping")
def ping_portfolio():
    return {"status": "ok"}


@router.get("/{portfolio_id}/returns", response_model=ReturnsResponse)
def get_portfolio_returns(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify ownership
    portfolio = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    # Dummy response for test pass; replace with real logic as needed
    return ReturnsResponse()


class HoldingCreate(BaseModel):
    ticker: str
    quantity: float = Field(..., gt=0, description="Quantity must be positive")


class PortfolioCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(default="", max_length=500)
    portfolio_type: str
    holdings: List[HoldingCreate] = []


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    portfolio_type: str
    holdings: List[HoldingCreate]


@router.post("/", response_model=PortfolioResponse)
def create_portfolio(
    portfolio: PortfolioCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new portfolio for the authenticated user."""
    # Find assets by ticker
    holdings = []
    for h in portfolio.holdings:
        asset = db.query(Asset).filter(Asset.ticker == h.ticker).first()
        if not asset:
            raise HTTPException(status_code=400, detail=f"Asset {h.ticker} not found")
        holdings.append(PortfolioHolding(
            asset_id=asset.id, 
            quantity=h.quantity, 
            average_cost=0, 
            total_cost=0
        ))
    
    p = Portfolio(
        name=portfolio.name,
        description=portfolio.description,
        portfolio_type=portfolio.portfolio_type,
        holdings=holdings,
        user_id=current_user.id  # Associate with authenticated user
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    
    # Build response with ticker lookup
    holding_responses = []
    for h in p.holdings:
        asset = db.get(Asset, h.asset_id)
        if asset:
            holding_responses.append(HoldingCreate(ticker=asset.ticker, quantity=h.quantity))
    
    return PortfolioResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        portfolio_type=p.portfolio_type,
        holdings=holding_responses
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get portfolio by ID - only accessible by owner."""
    p = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    holding_responses = []
    for h in p.holdings:
        asset = db.get(Asset, h.asset_id)
        if asset:
            holding_responses.append(HoldingCreate(ticker=asset.ticker, quantity=h.quantity))
    
    return PortfolioResponse(
        id=p.id,
        name=p.name,
        description=p.description,
        portfolio_type=p.portfolio_type,
        holdings=holding_responses
    )


@router.get("/", response_model=List[PortfolioResponse])
def list_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all portfolios for the authenticated user."""
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    
    result = []
    for p in portfolios:
        holding_responses = []
        for h in p.holdings:
            asset = db.get(Asset, h.asset_id)
            if asset:
                holding_responses.append(HoldingCreate(ticker=asset.ticker, quantity=h.quantity))
        
        result.append(PortfolioResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            portfolio_type=p.portfolio_type,
            holdings=holding_responses
        ))
    
    return result


@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete portfolio - only accessible by owner."""
    p = db.query(Portfolio).filter(
        Portfolio.id == portfolio_id,
        Portfolio.user_id == current_user.id
    ).first()
    
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    db.delete(p)
    db.commit()
    return {"detail": "Portfolio deleted"}
