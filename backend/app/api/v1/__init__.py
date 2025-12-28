"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1.endpoints import valuation, optimization, bitemporal, portfolio, market_data, auth

api_router = APIRouter()

api_router.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
api_router.include_router(bitemporal.router, prefix="/bitemporal", tags=["bitemporal"])
api_router.include_router(portfolio.router, prefix="/portfolios", tags=["portfolio"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
