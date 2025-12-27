"""Valuation endpoints - CM1 module."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

from app.services.actuarial import BondPricer, DCFValuation, AnnuityCalculator

router = APIRouter()


class BondPriceRequest(BaseModel):
    """Request model for bond pricing."""
    face_value: float = Field(..., gt=0, description="Face value")
    coupon_rate: float = Field(..., ge=0, le=1, description="Annual coupon rate")
    yield_rate: float = Field(..., gt=0, description="Yield to maturity")
    years_to_maturity: float = Field(..., gt=0, description="Years to maturity")
    frequency: int = Field(2, description="Coupon frequency per year")


class BondPriceResponse(BaseModel):
    """Response model for bond pricing."""
    price: float
    macaulay_duration: float
    modified_duration: float


class DCFRequest(BaseModel):
    """Request model for DCF valuation."""
    initial_fcf: float = Field(..., description="Initial free cash flow")
    growth_rates: List[float] = Field(..., description="Growth rates for forecast period")
    terminal_growth: float = Field(..., ge=0, le=0.1, description="Terminal growth rate")
    risk_free_rate: float = Field(0.20, description="Risk-free rate")
    beta: float = Field(1.0, description="Beta coefficient")
    market_return: float = Field(0.15, description="Expected market return")


@router.post("/bond/price", response_model=BondPriceResponse)
async def price_bond(request: BondPriceRequest):
    """
    Calculate bond price and duration metrics.
    
    Uses standard bond pricing formula with semi-annual coupons.
    """
    try:
        price = BondPricer.bond_price(
            face_value=request.face_value,
            coupon_rate=request.coupon_rate,
            yield_rate=request.yield_rate,
            years_to_maturity=request.years_to_maturity,
            frequency=request.frequency
        )
        
        duration_mac = BondPricer.macaulay_duration(
            face_value=request.face_value,
            coupon_rate=request.coupon_rate,
            yield_rate=request.yield_rate,
            years_to_maturity=request.years_to_maturity,
            frequency=request.frequency
        )
        
        duration_mod = BondPricer.modified_duration(
            face_value=request.face_value,
            coupon_rate=request.coupon_rate,
            yield_rate=request.yield_rate,
            years_to_maturity=request.years_to_maturity,
            frequency=request.frequency
        )
        
        return BondPriceResponse(
            price=round(price, 2),
            macaulay_duration=round(duration_mac, 4),
            modified_duration=round(duration_mod, 4)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/equity/dcf")
async def dcf_valuation(request: DCFRequest):
    """
    Multi-stage DCF valuation with Zambian market adjustments.
    
    Includes Country Risk Premium (CRP) in WACC calculation.
    """
    try:
        # Calculate WACC
        wacc = DCFValuation.wacc_zambian(
            risk_free_rate=request.risk_free_rate,
            beta=request.beta,
            market_return=request.market_return
        )
        
        # DCF valuation
        enterprise_value = DCFValuation.dcf_multistage(
            initial_fcf=request.initial_fcf,
            growth_rates=request.growth_rates,
            terminal_growth=request.terminal_growth,
            wacc=wacc
        )
        
        return {
            "enterprise_value": round(enterprise_value, 2),
            "wacc": round(wacc, 4),
            "forecast_years": len(request.growth_rates),
            "assumptions": {
                "risk_free_rate": request.risk_free_rate,
                "beta": request.beta,
                "market_return": request.market_return,
                "zambian_crp": 0.05
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/annuity/{annuity_type}")
async def calculate_annuity(
    annuity_type: str,
    interest_rate: float = Field(..., gt=0, description="Interest rate"),
    periods: int = Field(..., gt=0, description="Number of periods")
):
    """
    Calculate annuity present value.
    
    Types: immediate, due, perpetuity
    """
    try:
        if annuity_type == "immediate":
            pv = AnnuityCalculator.annuity_immediate(interest_rate, periods)
        elif annuity_type == "due":
            pv = AnnuityCalculator.annuity_due(interest_rate, periods)
        elif annuity_type == "perpetuity":
            pv = AnnuityCalculator.perpetuity(interest_rate)
        else:
            raise ValueError(f"Unknown annuity type: {annuity_type}")
        
        return {
            "present_value": round(pv, 4),
            "type": annuity_type,
            "interest_rate": interest_rate,
            "periods": periods if annuity_type != "perpetuity" else "infinite"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bond/ytm")
async def calculate_ytm(
    price: float = Field(..., gt=0),
    face_value: float = Field(..., gt=0),
    coupon_rate: float = Field(..., ge=0, le=1),
    years_to_maturity: float = Field(..., gt=0),
    frequency: int = Field(2)
):
    """Calculate Yield to Maturity using Newton-Raphson method."""
    try:
        ytm = BondPricer.yield_to_maturity(
            price=price,
            face_value=face_value,
            coupon_rate=coupon_rate,
            years_to_maturity=years_to_maturity,
            frequency=frequency
        )
        
        return {
            "yield_to_maturity": round(ytm, 6),
            "annual_percentage": round(ytm * 100, 4)
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
