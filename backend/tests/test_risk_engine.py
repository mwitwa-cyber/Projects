"""
Tests for RiskEngine service.

Tests cover:
- Beta calculation
- VaR calculation
- Data transformation (resampling, returns)
- Edge cases (insufficient data, zero variance)
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, MagicMock, AsyncMock, patch

from app.services.analytics import (
    RiskEngine,
    RiskMetrics,
    RiskCalculationError,
    convert_prices_to_dataframe,
    prepare_returns_data,
    calculate_beta,
    calculate_var_95,
    get_risk_metrics_sync
)


# ==================== Fixtures ====================

@pytest.fixture
def sample_price_data():
    """Generate sample price history mimicking PriceHistory model."""
    
    class MockPriceHistory:
        def __init__(self, trade_date, close_price, asset_id=1):
            self.trade_date = trade_date
            self.close_price = close_price
            self.asset_id = asset_id
            self.is_current = True
    
    # Generate 100 trading days of data
    base_date = date(2025, 1, 1)
    dates = [base_date + timedelta(days=i) for i in range(100)]
    
    # Asset prices: starting at 100, random walk
    np.random.seed(42)
    asset_returns = np.random.normal(0.001, 0.02, 100)
    asset_prices = 100 * np.cumprod(1 + asset_returns)
    
    # Benchmark prices: correlated with asset
    benchmark_returns = 0.7 * asset_returns + 0.3 * np.random.normal(0.001, 0.015, 100)
    benchmark_prices = 100 * np.cumprod(1 + benchmark_returns)
    
    asset_records = [
        MockPriceHistory(d, p, asset_id=1)
        for d, p in zip(dates, asset_prices)
    ]
    
    benchmark_records = [
        MockPriceHistory(d, p, asset_id=2)
        for d, p in zip(dates, benchmark_prices)
    ]
    
    return asset_records, benchmark_records


@pytest.fixture
def sparse_price_data():
    """Generate sparse price data (simulating LuSE illiquidity)."""
    
    class MockPriceHistory:
        def __init__(self, trade_date, close_price, asset_id=1):
            self.trade_date = trade_date
            self.close_price = close_price
            self.asset_id = asset_id
            self.is_current = True
    
    # Only trade on some days (sparse)
    base_date = date(2025, 1, 1)
    trading_days = [0, 2, 5, 7, 12, 15, 19, 22, 26, 30, 35, 40, 45, 50, 55, 60, 65, 70]
    
    dates = [base_date + timedelta(days=i) for i in trading_days]
    prices = [100, 101, 99, 102, 100, 103, 101, 104, 102, 105, 103, 106, 104, 107, 105, 108, 106, 109]
    
    return [MockPriceHistory(d, p) for d, p in zip(dates, prices)]


# ==================== Unit Tests: Helper Functions ====================

class TestConvertPricesToDataframe:
    """Tests for convert_prices_to_dataframe function."""
    
    def test_basic_conversion(self, sample_price_data):
        """Test basic conversion from price records to DataFrame."""
        asset_records, _ = sample_price_data
        
        df = convert_prices_to_dataframe(asset_records)
        
        assert isinstance(df, pd.DataFrame)
        assert "close" in df.columns
        assert len(df) == 100
        assert isinstance(df.index, pd.DatetimeIndex)
    
    def test_empty_prices(self):
        """Test handling of empty price list."""
        df = convert_prices_to_dataframe([])
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "close" in df.columns
    
    def test_sorted_index(self, sample_price_data):
        """Test that DataFrame index is sorted."""
        asset_records, _ = sample_price_data
        
        # Shuffle records
        np.random.shuffle(asset_records)
        
        df = convert_prices_to_dataframe(asset_records)
        
        assert df.index.is_monotonic_increasing


class TestPrepareReturnsData:
    """Tests for prepare_returns_data function."""
    
    def test_weekly_resampling(self, sample_price_data):
        """Test that data is properly resampled to weekly frequency."""
        asset_records, benchmark_records = sample_price_data
        
        asset_df = convert_prices_to_dataframe(asset_records)
        benchmark_df = convert_prices_to_dataframe(benchmark_records)
        
        asset_returns, benchmark_returns = prepare_returns_data(
            asset_df, benchmark_df, resample_freq="W"
        )
        
        # Should have fewer observations after weekly resampling
        assert len(asset_returns) < len(asset_df)
        # Weekly data from ~100 days should give ~14 weeks
        assert 10 <= len(asset_returns) <= 20
    
    def test_returns_alignment(self, sample_price_data):
        """Test that returns are properly aligned."""
        asset_records, benchmark_records = sample_price_data
        
        asset_df = convert_prices_to_dataframe(asset_records)
        benchmark_df = convert_prices_to_dataframe(benchmark_records)
        
        asset_returns, benchmark_returns = prepare_returns_data(
            asset_df, benchmark_df
        )
        
        # Should have same length and index
        assert len(asset_returns) == len(benchmark_returns)
        assert all(asset_returns.index == benchmark_returns.index)
    
    def test_log_returns(self, sample_price_data):
        """Test that log returns are calculated correctly."""
        asset_records, benchmark_records = sample_price_data
        
        asset_df = convert_prices_to_dataframe(asset_records)
        benchmark_df = convert_prices_to_dataframe(benchmark_records)
        
        asset_returns, _ = prepare_returns_data(asset_df, benchmark_df)
        
        # Log returns should be roughly bounded
        assert all(asset_returns > -1)  # Can't lose more than 100%
        assert all(asset_returns < 1)   # Unlikely to gain more than 100% in a week


class TestCalculateBeta:
    """Tests for calculate_beta function."""
    
    def test_beta_calculation(self):
        """Test basic beta calculation."""
        # Perfect positive correlation should give beta ~1
        np.random.seed(42)
        benchmark = pd.Series(np.random.normal(0, 0.02, 52))
        asset = 1.2 * benchmark + np.random.normal(0, 0.005, 52)  # Beta ~1.2
        
        beta = calculate_beta(asset, benchmark)
        
        assert 1.0 <= beta <= 1.4  # Should be close to 1.2
    
    def test_beta_zero_variance_error(self):
        """Test that zero variance raises error."""
        asset = pd.Series([0.01, 0.02, 0.01, 0.02])
        benchmark = pd.Series([0.0, 0.0, 0.0, 0.0])  # Zero variance
        
        with pytest.raises(RiskCalculationError) as exc_info:
            calculate_beta(asset, benchmark)
        
        assert exc_info.value.error_code == "ZERO_VARIANCE"
    
    def test_beta_insufficient_data(self):
        """Test that insufficient data raises error."""
        asset = pd.Series([0.01])
        benchmark = pd.Series([0.02])
        
        with pytest.raises(RiskCalculationError) as exc_info:
            calculate_beta(asset, benchmark)
        
        assert exc_info.value.error_code == "INSUFFICIENT_DATA"


class TestCalculateVar95:
    """Tests for calculate_var_95 function."""
    
    def test_var_calculation(self):
        """Test VaR calculation with known distribution."""
        # Normal distribution with mean 0, std 0.02
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 1000))
        
        var = calculate_var_95(returns)
        
        # 5th percentile of N(0, 0.02) is approximately -0.0329
        # As percentage: -3.29%
        assert -5 < var < -2  # Should be negative (loss)
    
    def test_var_insufficient_data(self):
        """Test that insufficient data raises error."""
        returns = pd.Series([0.01, 0.02, 0.01])  # Only 3 points
        
        with pytest.raises(RiskCalculationError) as exc_info:
            calculate_var_95(returns)
        
        assert exc_info.value.error_code == "INSUFFICIENT_DATA"
    
    def test_var_returns_percentage(self):
        """Test that VaR is returned as percentage."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0, 0.02, 100))
        
        var = calculate_var_95(returns)
        
        # Should be in percentage range, not decimal
        assert abs(var) > 0.1  # Should be > 0.1%


# ==================== Integration Tests: RiskEngine ====================

class TestRiskEngineSync:
    """Tests for RiskEngine synchronous operations."""
    
    def test_calculate_risk_metrics_sync(self, sample_price_data):
        """Test full risk metrics calculation (sync)."""
        asset_records, benchmark_records = sample_price_data
        
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            asset_records,
            benchmark_records
        ]
        
        engine = RiskEngine(mock_db)
        
        metrics = engine.calculate_risk_metrics_sync(
            asset_id=1,
            benchmark_id=2,
            lookback_days=365
        )
        
        assert isinstance(metrics, RiskMetrics)
        assert isinstance(metrics.beta, float)
        assert isinstance(metrics.var_95, float)
        assert metrics.observation_count > 0
        assert metrics.asset_id == 1
        assert metrics.benchmark_id == 2
    
    def test_no_asset_data_error(self):
        """Test error when no asset data is found."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            [],  # No asset data
            []
        ]
        
        engine = RiskEngine(mock_db)
        
        with pytest.raises(RiskCalculationError) as exc_info:
            engine.calculate_risk_metrics_sync(1, 2, 365)
        
        assert exc_info.value.error_code == "NO_ASSET_DATA"
    
    def test_insufficient_observations_error(self, sparse_price_data):
        """Test error when insufficient observations after resampling."""
        # Create very sparse data that won't yield enough weekly observations
        class MockPriceHistory:
            def __init__(self, trade_date, close_price, asset_id=1):
                self.trade_date = trade_date
                self.close_price = close_price
                self.asset_id = asset_id
                self.is_current = True
        
        # Only 3 weeks of data
        dates = [date(2025, 1, 1) + timedelta(days=i*7) for i in range(5)]
        asset_data = [MockPriceHistory(d, 100 + i) for i, d in enumerate(dates)]
        benchmark_data = [MockPriceHistory(d, 100 + i*0.5) for i, d in enumerate(dates)]
        
        # Pad with minimum required points
        for i in range(15):
            extra_date = date(2025, 1, 1) + timedelta(days=i)
            if extra_date not in dates:
                asset_data.append(MockPriceHistory(extra_date, 100))
                benchmark_data.append(MockPriceHistory(extra_date, 100))
        
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [
            asset_data,
            benchmark_data
        ]
        
        engine = RiskEngine(mock_db)
        
        with pytest.raises(RiskCalculationError) as exc_info:
            engine.calculate_risk_metrics_sync(1, 2, 365)
        
        assert exc_info.value.error_code == "INSUFFICIENT_OBSERVATIONS"


@pytest.mark.asyncio
class TestRiskEngineAsync:
    """Tests for RiskEngine asynchronous operations."""
    
    async def test_calculate_risk_metrics_async(self, sample_price_data):
        """Test full risk metrics calculation (async)."""
        asset_records, benchmark_records = sample_price_data
        
        # Mock async database session
        mock_db = AsyncMock()
        
        # Mock the execute and scalars chain
        mock_result = Mock()
        mock_result.scalars.return_value.all.side_effect = [
            asset_records,
            benchmark_records
        ]
        mock_db.execute.return_value = mock_result
        
        engine = RiskEngine(mock_db)
        
        metrics = await engine.calculate_risk_metrics(
            asset_id=1,
            benchmark_id=2,
            lookback_days=365
        )
        
        assert isinstance(metrics, RiskMetrics)
        assert isinstance(metrics.beta, float)
        assert isinstance(metrics.var_95, float)
        assert metrics.observation_count > 0


# ==================== Schema Tests ====================

class TestRiskMetricsSchema:
    """Tests for RiskMetrics Pydantic schema."""
    
    def test_valid_schema(self):
        """Test valid schema instantiation."""
        metrics = RiskMetrics(
            beta=1.25,
            var_95=-3.45,
            observation_count=52,
            calculation_date=datetime.utcnow(),
            asset_id=1,
            benchmark_id=2,
            lookback_days=365
        )
        
        assert metrics.beta == 1.25
        assert metrics.var_95 == -3.45
        assert metrics.observation_count == 52
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        metrics = RiskMetrics(
            beta=1.25,
            var_95=-3.45,
            observation_count=52,
            calculation_date=datetime(2026, 1, 3, 10, 30, 0),
            asset_id=1,
            benchmark_id=2,
            lookback_days=365
        )
        
        json_data = metrics.model_dump()
        
        assert "beta" in json_data
        assert "var_95" in json_data
        assert "observation_count" in json_data


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_highly_correlated_assets(self):
        """Test beta calculation with highly correlated assets."""
        np.random.seed(42)
        benchmark = pd.Series(np.random.normal(0, 0.02, 52))
        asset = benchmark + np.random.normal(0, 0.001, 52)  # Almost identical
        
        beta = calculate_beta(asset, benchmark)
        
        # Beta should be very close to 1
        assert 0.95 <= beta <= 1.05
    
    def test_negative_beta(self):
        """Test beta calculation with negatively correlated assets."""
        np.random.seed(42)
        benchmark = pd.Series(np.random.normal(0, 0.02, 52))
        asset = -0.5 * benchmark + np.random.normal(0, 0.005, 52)
        
        beta = calculate_beta(asset, benchmark)
        
        # Beta should be negative
        assert beta < 0
    
    def test_defensive_stock(self):
        """Test beta calculation for defensive stock (beta < 1)."""
        np.random.seed(42)
        benchmark = pd.Series(np.random.normal(0, 0.02, 52))
        asset = 0.5 * benchmark + np.random.normal(0, 0.005, 52)
        
        beta = calculate_beta(asset, benchmark)
        
        # Beta should be less than 1
        assert 0 < beta < 1
