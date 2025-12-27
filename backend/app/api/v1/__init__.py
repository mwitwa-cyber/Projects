"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1.endpoints import valuation, optimization

api_router = APIRouter()

api_router.include_router(valuation.router, prefix="/valuation", tags=["valuation"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
