from fastapi import APIRouter, HTTPException
from app.services.valuation import ValuationService
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class BondParams(BaseModel):
    face_value: float = 100.0
    coupon_rate: float
    market_yield: float
    years_to_maturity: float
    frequency: int = 2

class Instrument(BaseModel):
    maturity: float
    rate: Optional[float] = None # For T-Bills
    coupon: Optional[float] = None # For Bonds
    price: Optional[float] = 100.0

class BootStrapRequest(BaseModel):
    instruments: List[Instrument]

@router.post("/bond-pricing")
def price_bond(params: BondParams):
    """
    Returns Price, Duration, and Convexity for a bond.
    """
    return ValuationService.bond_pricing(
        params.face_value, 
        params.coupon_rate, 
        params.market_yield, 
        params.years_to_maturity, 
        params.frequency
    )

@router.post("/yield-curve")
def bootstrap_curve(request: BootStrapRequest):
    """
    Bootstraps the Zero Coupon Yield Curve from market instruments.
    """
    data = [i.dict() for i in request.instruments]
    return ValuationService.bootstrap_yield_curve(data)

@router.get("/grz-curve-sample")
def get_sample_curve():
    """
    Returns a sample GRZ yield curve based on typical 2024 rates.
    """
    instruments = [
        {"maturity": 0.25, "rate": 0.15}, # 91d T-Bill
        {"maturity": 0.5, "rate": 0.16},  # 182d T-Bill
        {"maturity": 1.0, "rate": 0.18},  # 364d T-Bill
        {"maturity": 2.0, "coupon": 0.22, "price": 100}, # 2yr Bond
        {"maturity": 5.0, "coupon": 0.24, "price": 100}, # 5yr Bond
        {"maturity": 10.0, "coupon": 0.26, "price": 100}, # 10yr Bond
    ]
    return ValuationService.bootstrap_yield_curve(instruments)
