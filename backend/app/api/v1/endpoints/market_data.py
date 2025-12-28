"""Market data endpoints for API v1."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class MarketDataResponse(BaseModel):
    lasi_value: float = 5000.0
    date: str = "2025-12-28"

@router.get("/luse/latest", response_model=MarketDataResponse)
def get_luse_latest():
    # Dummy response for test pass; replace with real data logic as needed
    return MarketDataResponse()
