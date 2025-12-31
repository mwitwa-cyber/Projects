"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_router
import logging
import sys
import os

# Configure logging
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
if settings.ENVIRONMENT == "production":
    LOG_FORMAT = '{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
    log_level = logging.WARNING
else:
    log_level = logging.INFO

logging.basicConfig(
    level=log_level,
    format=LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app")

# Optional: background scraper import
try:
    from app.services.scraper import run_background_scraper
except ImportError:
    run_background_scraper = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    import asyncio
    
    # Startup
    logger.info("Starting LuSE Quantitative Platform...")
    
    # Initialize Redis Cache
    try:
        from fastapi_cache import FastAPICache
        from fastapi_cache.backends.redis import RedisBackend
        from redis import asyncio as aioredis
        
        redis = aioredis.from_url(
            settings.REDIS_CACHE_URL, 
            encoding="utf8", 
            decode_responses=True
        )
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
        logger.info("Redis cache initialized")
    except Exception as e:
        logger.warning(f"Redis cache initialization failed: {e}")
    
    # Start background scraper if enabled
    scraper_task = None
    if os.getenv("ENABLE_SCRAPER", "false").lower() in ("1", "true", "yes") and run_background_scraper:
        provider = os.getenv("SCRAPER_PROVIDER")
        interval = os.getenv("SCRAPER_INTERVAL")
        scraper_task = asyncio.create_task(run_background_scraper(provider, interval))
        logger.info(f"Background scraper started with provider: {provider}")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down LuSE Quantitative Platform...")
    if scraper_task:
        scraper_task.cancel()
        try:
            await scraper_task
        except asyncio.CancelledError:
            pass


# Create FastAPI app with lifespan manager
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# CORS middleware with stricter settings for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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
