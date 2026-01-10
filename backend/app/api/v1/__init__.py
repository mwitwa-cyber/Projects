"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1.endpoints import valuation, optimization, portfolio, market_data, auth, monitoring, analytics, backtest, reports

api_router = APIRouter()

api_router.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
# api_router.include_router(bitemporal.router, prefix="/bitemporal", tags=["bitemporal"])
api_router.include_router(portfolio.router, prefix="/portfolios", tags=["portfolio"])
api_router.include_router(market_data.router, prefix="/market-data", tags=["market-data"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(monitoring.router, tags=["monitoring"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
