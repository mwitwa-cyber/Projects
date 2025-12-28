"""Bitemporal API endpoints for temporal data queries.

Provides REST endpoints for temporal data operations.
"""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.services.bitemporal_service import BitemporalService


router = APIRouter()


# ==================== Request/Response Models ====================

class PriceCorrection(BaseModel):
    """Request model for price correction."""
    asset_id: int
    trade_date: date
    corrected_close_price: float
    corrected_open_price: Optional[float] = None
    corrected_high_price: Optional[float] = None
    corrected_low_price: Optional[float] = None
    corrected_volume: Optional[float] = None
    correction_reason: Optional[str] = None


class PriceResponse(BaseModel):
    """Response model for price data."""
    asset_id: int
    trade_date: date
    close_price: float
    open_price: Optional[float]
    high_price: Optional[float]
    low_price: Optional[float]
    volume: Optional[float]
    valid_from: datetime
    valid_to: Optional[datetime]
    transaction_from: datetime
    transaction_to: Optional[datetime]
    is_current: bool
    
    class Config:
        from_attributes = True


class CorrectionAudit(BaseModel):
    """Response model for correction audit."""
    trade_date: date
    corrected_at: datetime
    old_close_price: float
    new_close_price: float
    price_change: float
    price_change_pct: Optional[float]


# ==================== Endpoints ====================

@router.get("/price/current/{asset_id}/{trade_date}", response_model=PriceResponse)
def get_current_price(
    asset_id: int,
    trade_date: date,
    db: Session = Depends(get_db)
):
    """Get the current version of price data for a specific date."""
    service = BitemporalService(db)
    price = service.get_current_price(asset_id, trade_date)
    
    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for asset {asset_id} on {trade_date}"
        )
    
    return price


@router.get("/price/as-of-transaction/{asset_id}/{trade_date}", response_model=PriceResponse)
def get_price_as_of_transaction(
    asset_id: int,
    trade_date: date,
    as_of: datetime = Query(..., description="Transaction time to query"),
    db: Session = Depends(get_db)
):
    """Get price data as it was recorded in the system at a specific time.
    
    This is critical for backtesting - it shows what data was available
    at the time the decision would have been made.
    """
    service = BitemporalService(db)
    price = service.get_price_as_of_transaction_time(asset_id, trade_date, as_of)
    
    if not price:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for asset {asset_id} on {trade_date} as of {as_of}"
        )
    
    return price


@router.get("/price/history/{asset_id}", response_model=List[PriceResponse])
def get_price_history(
    asset_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    as_of_transaction: Optional[datetime] = Query(
        None, 
        description="Optional transaction time for historical view"
    ),
    db: Session = Depends(get_db)
):
    """Get price history for a date range.
    
    If as_of_transaction is provided, returns data as it existed in the
    system at that time (for backtesting).
    """
    service = BitemporalService(db)
    prices = service.get_price_history_range(
        asset_id, 
        start_date, 
        end_date,
        as_of_transaction
    )
    
    return prices


@router.post("/price/correct", response_model=PriceResponse)
def correct_price(
    correction: PriceCorrection,
    db: Session = Depends(get_db)
):
    """Correct an existing price record while preserving history.
    
    This creates a new version of the price record with corrected data,
    while keeping the old version for audit purposes.
    """
    service = BitemporalService(db)
    
    try:
        corrected_price = service.correct_price(
            asset_id=correction.asset_id,
            trade_date=correction.trade_date,
            corrected_close_price=correction.corrected_close_price,
            corrected_open_price=correction.corrected_open_price,
            corrected_high_price=correction.corrected_high_price,
            corrected_low_price=correction.corrected_low_price,
            corrected_volume=correction.corrected_volume
        )
        return corrected_price
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/audit/corrections/{asset_id}", response_model=List[CorrectionAudit])
def get_corrections_audit(
    asset_id: int,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db)
):
    """Get an audit trail of all price corrections for an asset.
    
    This is useful for compliance and understanding data quality.
    """
    service = BitemporalService(db)
    corrections = service.get_corrections_audit(asset_id, start_date, end_date)
    
    return corrections


@router.get("/health")
def bitemporal_health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "bitemporal",
        "capabilities": [
            "point_in_time_queries",
            "transaction_time_queries",
            "price_corrections",
            "audit_trail"
        ]
    }
