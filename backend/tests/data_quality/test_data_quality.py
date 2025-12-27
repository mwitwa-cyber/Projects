"""
Data quality validation tests for LUSE prices, transactions, yield curve, and timestamps.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.price_history import PriceHistory
from app.models.yield_curve import YieldCurveData

engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)

@pytest.mark.data_quality
def test_luse_prices_within_bounds():
    session = Session()
    prices = session.query(PriceHistory).all()
    for p in prices:
        assert p.close_price > 0 and p.close_price < 1_000_000
        assert p.volume is None or p.volume >= 0
    session.close()

@pytest.mark.data_quality
def test_no_orphaned_transactions():
    session = Session()
    orphaned = session.query(PriceHistory).filter(PriceHistory.asset_id == None).count()
    assert orphaned == 0
    session.close()

@pytest.mark.data_quality
def test_yield_curve_monotonicity():
    session = Session()
    curves = session.query(YieldCurveData).order_by(YieldCurveData.observation_date, YieldCurveData.tenor_days).all()
    last_date = None
    last_yield = -1
    for yc in curves:
        if yc.observation_date != last_date:
            last_date = yc.observation_date
            last_yield = -1
        assert yc.yield_rate >= last_yield
        last_yield = yc.yield_rate
    session.close()

@pytest.mark.data_quality
def test_timestamp_consistency():
    session = Session()
    prices = session.query(PriceHistory).all()
    for p in prices:
        assert p.trade_date is not None
        assert p.valid_from <= p.transaction_from
    session.close()
