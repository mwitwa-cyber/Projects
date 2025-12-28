"""Bitemporal API endpoints for temporal data queries.

Provides REST endpoints for temporal data operations.
"""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.bitemporal_service import BitemporalService


router = APIRouter()


class PriceCorrection(BaseModel):
    asset_id: int
    trade_date: date
    corrected_close_price: float
    corrected_open_price: Optional[float] = None
    corrected_high_price: Optional[float] = None
    corrected_low_price: Optional[float] = None
    corrected_volume: Optional[float] = None
    correction_reason: Optional[str] = None


class PriceResponse(BaseModel):
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
    trade_date: date
    corrected_at: datetime
    old_close_price: float
    new_close_price: float
    price_change: float
    price_change_pct: Optional[float]


@router.get("/price/current/{asset_id}/{trade_date}", response_model=PriceResponse)
def get_current_price(
    asset_id: int,
    trade_date: date,
    db: Session = Depends(get_db)
):
    service = BitemporalService(db)
    price = service.get_current_price(asset_id, trade_date)

    if not price:
        raise HTTPException(status_code=404, detail=f"No price data found for asset {asset_id} on {trade_date}")

    return price


@router.get("/price/as-of-transaction/{asset_id}/{trade_date}", response_model=PriceResponse)
def get_price_as_of_transaction(
    asset_id: int,
    trade_date: date,
    as_of: datetime = Query(..., description="Transaction time to query"),
    db: Session = Depends(get_db)
):
    service = BitemporalService(db)
    price = service.get_price_as_of_transaction_time(asset_id, trade_date, as_of)

    if not price:
        raise HTTPException(status_code=404, detail=f"No price data found for asset {asset_id} on {trade_date} as of {as_of}")

    return price


@router.get("/price/history/{asset_id}", response_model=List[PriceResponse])
def get_price_history(
    asset_id: int,
    start_date: date = Query(..., description="Start date"),
    end_date: date = Query(..., description="End date"),
    as_of_transaction: Optional[datetime] = Query(None, description="Optional transaction time for historical view"),
    db: Session = Depends(get_db)
):
    service = BitemporalService(db)
    prices = service.get_price_history_range(asset_id, start_date, end_date, as_of_transaction)
    return prices


@router.post("/price/correct", response_model=PriceResponse)
def correct_price(
    correction: PriceCorrection,
    db: Session = Depends(get_db)
):
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
    service = BitemporalService(db)
    corrections = service.get_corrections_audit(asset_id, start_date, end_date)
    return corrections


@router.get("/health")
def bitemporal_health():
    return {
        "status": "healthy",
        "service": "bitemporal",
        "capabilities": [
            "point_in_time_queries",
            "transaction_time_queries",
            "price_corrections",
            "audit_trail",
        ],
    }
