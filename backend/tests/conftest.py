import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.portfolio import Portfolio

# Use test database or fallback to local
TEST_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/luse_quant")

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    # Base.metadata.drop_all(bind=engine) # Optional: Clean up after tests

@pytest.fixture(scope="module")
def client():
    """Test client fixture."""
    # Override get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
