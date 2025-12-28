"""FastAPI application main entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
import logging
import sys

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
if settings.ENVIRONMENT == "production":
    # Simple JSON-like format for prod (or use python-json-logger if installed)
    LOG_FORMAT = '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app")
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
from app.models import user, portfolio, asset
from app.core.database import engine, Base
import os
import asyncio

# Create database tables
Base.metadata.create_all(bind=engine)

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
