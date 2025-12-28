"""FastAPI application main entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import market_data, valuation
from app.core import models
from app.core.db import engine
import os
import asyncio

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Optional: start background market-data scraper
try:
    from app.services.scraper import run_background_scraper
except Exception:
    run_background_scraper = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "LuSE Quantitative Investment Analysis Platform API"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": "v1"
    }


@app.on_event("startup")
async def startup_tasks():
    # If ENABLE_SCRAPER is set (True/1/yes), start background scraper
    if os.getenv("ENABLE_SCRAPER", "false").lower() in ("1", "true", "yes") and run_background_scraper:
        provider = os.getenv("SCRAPER_PROVIDER")
        interval = os.getenv("SCRAPER_INTERVAL")
        # schedule background scraper but don't await it
        asyncio.create_task(run_background_scraper(provider, interval))
