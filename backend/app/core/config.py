"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "LuSE Quantitative Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_CACHE_URL: str = "redis://redis:6379/1"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173", 
        "http://localhost:5174",
        "http://localhost:3000", 
        "http://localhost", 
        "http://localhost:80", 
        "http://127.0.0.1", 
        "http://127.0.0.1:80"
    ]
    
    # Security
    SECRET_KEY: str = ""  # Will be validated
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour (reduced from 24 for security)
    
    # Market Data
    LUSE_DATA_URL: str = "https://afx.kwayisi.org/luse/"
    BOZ_YIELD_URL: str = "https://www.boz.zm"
    
    # Calculation Parameters
    DEFAULT_RISK_FREE_RATE: float = 0.20  # 20% - typical ZMW T-bill rate
    DEFAULT_MARKET_RETURN: float = 0.15   # 15% - historical LASI return
    ZAMBIAN_CRP: float = 0.05             # 5% - Country Risk Premium
    
    # Optimization
    MAX_PORTFOLIO_SIZE: int = 50
    OPTIMIZATION_SOLVER: str = "ECOS"  # ECOS, OSQP, SCS
    
    # Risk Calculation Settings
    RISK_CALCULATION_HOUR: int = 18  # 6 PM - after market close
    RISK_CALCULATION_MINUTE: int = 30
    DEFAULT_LOOKBACK_DAYS: int = 365
    MIN_OBSERVATIONS_REQUIRED: int = 20  # Minimum weekly data points
    BENCHMARK_ASSET_ID: int = 1  # LASI index proxy
    
    # Celery
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"
    
    # Market Data Scraper
    ENABLE_SCRAPER: bool = True  # Enable background price fetching
    SCRAPER_PROVIDER: str = "luse"  # Use LuSE/AfricanFinancials provider
    SCRAPER_INTERVAL: int = 3600  # Fetch every hour (3600 seconds)
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Ensure SECRET_KEY is set and sufficiently strong in production."""
        if not v or v in ('', 'dev_secret', 'your-secret-key-change-in-production'):
            # In development, generate a random key with warning
            import logging
            logging.warning(
                "SECRET_KEY not set or using default. "
                "Generating random key. Set SECRET_KEY in production!"
            )
            return secrets.token_urlsafe(32)
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
