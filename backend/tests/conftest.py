"""Pytest configuration and fixtures."""

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

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
