"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


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
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
