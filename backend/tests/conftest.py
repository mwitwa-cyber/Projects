import pytest
from app.models.asset import Asset, AssetType, Sector
@pytest.fixture(scope="session", autouse=True)
def seed_assets(db_session):
    """Seed required assets for integration tests."""
    tickers = [
        {"ticker": "ZCCM-IH", "name": "ZCCM Investments Holdings", "asset_type": AssetType.EQUITY, "sector": Sector.MINING},
        {"ticker": "Zanaco", "name": "Zambia National Commercial Bank", "asset_type": AssetType.EQUITY, "sector": Sector.BANKING},
    ]
    for t in tickers:
        if not db_session.query(Asset).filter_by(ticker=t["ticker"]).first():
            asset = Asset(
                ticker=t["ticker"],
                name=t["name"],
                asset_type=t["asset_type"],
                sector=t["sector"]
            )
            db_session.add(asset)
    db_session.commit()
"""Pytest configuration and fixtures."""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base

# Import the models package to ensure all models are registered
import app.models

import os
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/luse_quant")

@pytest.fixture(scope="session")
def db_session():
    """Create a test database session with all tables for the session."""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
