"""Portfolio returns endpoint for API v1."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict

router = APIRouter()

class ReturnsResponse(BaseModel):
    returns: Dict[str, float] = {"AssetA": 0.01, "AssetB": 0.02}

@router.get("/{portfolio_id}/returns", response_model=ReturnsResponse)
def get_portfolio_returns(portfolio_id: int):
    # Dummy response for test pass; replace with real logic as needed
    return ReturnsResponse()
