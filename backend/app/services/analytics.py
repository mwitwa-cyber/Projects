"""
Risk Analytics Service for LuSE Quantitative Investment Platform.

Implements risk metrics calculations including:
- Beta coefficient (systematic risk)
- Value at Risk (VaR) using historical simulation
- Portfolio risk aggregation

Designed for LuSE market characteristics:
- Sparse trading (illiquid stocks)
- Weekly resampling to handle missing data
- Forward-fill for price gaps
"""

import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Tuple, Dict, Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.price_history import PriceHistory
from app.models.asset import Asset

logger = logging.getLogger(__name__)


# ==================== Pydantic Schemas ====================

class RiskMetrics(BaseModel):
    """Risk metrics output schema."""
    
    beta: float = Field(..., description="Beta coefficient vs benchmark")
    var_95: float = Field(..., description="95% Value at Risk as percentage")
    observation_count: int = Field(..., description="Number of weekly observations used")
    calculation_date: datetime = Field(..., description="Timestamp of calculation")
    
    # Additional context
    asset_id: int = Field(..., description="Asset identifier")
    benchmark_id: int = Field(..., description="Benchmark asset identifier")
    lookback_days: int = Field(..., description="Lookback period in days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "beta": 1.25,
                "var_95": -3.45,
                "observation_count": 52,
                "calculation_date": "2026-01-03T10:30:00",
                "asset_id": 1,
                "benchmark_id": 2,
                "lookback_days": 365
            }
        }


class RiskCalculationError(Exception):
    """Custom exception for risk calculation errors."""
    
    def __init__(self, message: str, error_code: str = "RISK_CALC_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


# ==================== Helper Functions ====================

def convert_prices_to_dataframe(
    prices: List[PriceHistory],
    date_column: str = "trade_date",
    price_column: str = "close_price"
) -> pd.DataFrame:
    """Convert SQLAlchemy price history records to Pandas DataFrame.
    
    Args:
        prices: List of PriceHistory model instances
        date_column: Name of date column in model
        price_column: Name of price column in model
        
    Returns:
        DataFrame with datetime index and 'close' column
    """
    if not prices:
        return pd.DataFrame(columns=["close"])
    
    data = [
        {
            "date": getattr(p, date_column),
            "close": getattr(p, price_column)
        }
        for p in prices
    ]
    
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    
    logger.debug(f"Converted {len(prices)} price records to DataFrame")
    return df


def prepare_returns_data(
    asset_df: pd.DataFrame,
    benchmark_df: pd.DataFrame,
    resample_freq: str = "W"
) -> Tuple[pd.Series, pd.Series]:
    """Prepare aligned log returns for risk calculations.
    
    Handles LuSE illiquidity by:
    1. Forward-filling missing prices
    2. Resampling to weekly frequency
    3. Calculating logarithmic returns
    4. Aligning asset and benchmark data
    
    Args:
        asset_df: DataFrame with asset prices (must have 'close' column)
        benchmark_df: DataFrame with benchmark prices
        resample_freq: Resampling frequency (default: 'W' for weekly)
        
    Returns:
        Tuple of (asset_returns, benchmark_returns) as aligned Series
    """
    # Forward-fill to handle trading gaps (LuSE illiquidity)
    asset_filled = asset_df["close"].ffill()
    benchmark_filled = benchmark_df["close"].ffill()
    
    # Resample to weekly (last price of the week)
    asset_weekly = asset_filled.resample(resample_freq).last()
    benchmark_weekly = benchmark_filled.resample(resample_freq).last()
    
    # Calculate logarithmic returns: log(P_t / P_t-1)
    asset_returns = np.log(asset_weekly / asset_weekly.shift(1))
    benchmark_returns = np.log(benchmark_weekly / benchmark_weekly.shift(1))
    
    # Align and drop NaN values
    combined = pd.concat(
        [asset_returns, benchmark_returns],
        axis=1,
        keys=["asset", "benchmark"],
        join="inner"
    ).dropna()
    
    logger.debug(
        f"Prepared returns: {len(combined)} weekly observations "
        f"from {combined.index.min()} to {combined.index.max()}"
    )
    
    return combined["asset"], combined["benchmark"]


def calculate_beta(
    asset_returns: pd.Series,
    benchmark_returns: pd.Series
) -> float:
    """Calculate beta coefficient.
    
    Beta = Cov(R_asset, R_benchmark) / Var(R_benchmark)
    
    Args:
        asset_returns: Series of asset log returns
        benchmark_returns: Series of benchmark log returns
        
    Returns:
        Beta coefficient
        
    Raises:
        RiskCalculationError: If variance is zero or data is insufficient
    """
    if len(asset_returns) < 2 or len(benchmark_returns) < 2:
        raise RiskCalculationError(
            "Insufficient data points for beta calculation",
            "INSUFFICIENT_DATA"
        )
    
    benchmark_variance = benchmark_returns.var()
    
    if benchmark_variance == 0 or np.isnan(benchmark_variance):
        raise RiskCalculationError(
            "Benchmark variance is zero - cannot calculate beta",
            "ZERO_VARIANCE"
        )
    
    covariance = asset_returns.cov(benchmark_returns)
    beta = covariance / benchmark_variance
    
    logger.debug(f"Calculated beta: {beta:.4f} (cov={covariance:.6f}, var={benchmark_variance:.6f})")
    
    return float(beta)


def calculate_var_95(returns: pd.Series) -> float:
    """Calculate 95% Value at Risk using historical simulation.
    
    VaR(95%) = 5th percentile of historical returns
    
    Args:
        returns: Series of log returns
        
    Returns:
        VaR as a percentage (negative value indicates loss)
        
    Raises:
        RiskCalculationError: If insufficient data
    """
    if len(returns) < 5:
        raise RiskCalculationError(
            "Insufficient data for VaR calculation (minimum 5 observations)",
            "INSUFFICIENT_DATA"
        )
    
    # 5th percentile of returns (left tail)
    var_95 = float(np.percentile(returns, 5))
    
    # Convert to percentage
    var_95_pct = var_95 * 100
    
    logger.debug(f"Calculated VaR(95%): {var_95_pct:.4f}%")
    
    return var_95_pct


# ==================== RiskEngine Service ====================

class RiskEngine:
    """Risk analytics engine for LuSE assets.
    
    Calculates risk metrics including Beta and VaR by:
    1. Fetching historical prices from TimescaleDB
    2. Transforming to weekly log returns
    3. Computing risk metrics with proper handling of illiquidity
    
    Supports both sync and async database sessions.
    
    Example:
        ```python
        # Async usage
        async with async_session() as db:
            engine = RiskEngine(db)
            metrics = await engine.calculate_risk_metrics(
                asset_id=1,
                benchmark_id=2,
                lookback_days=365
            )
        
        # Sync usage
        with Session() as db:
            engine = RiskEngine(db)
            metrics = engine.calculate_risk_metrics_sync(
                asset_id=1,
                benchmark_id=2,
                lookback_days=365
            )
        ```
    """
    
    def __init__(self, db: Session | AsyncSession):
        """Initialize RiskEngine with database session.
        
        Args:
            db: SQLAlchemy session (sync or async)
        """
        self.db = db
        logger.info("RiskEngine initialized")
    
    async def _fetch_prices_async(
        self,
        asset_id: int,
        start_date: date,
        end_date: date
    ) -> List[PriceHistory]:
        """Fetch price history using async SQLAlchemy.
        
        Args:
            asset_id: Asset identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of PriceHistory records
        """
        stmt = select(PriceHistory).where(
            and_(
                PriceHistory.asset_id == asset_id,
                PriceHistory.trade_date >= start_date,
                PriceHistory.trade_date <= end_date,
                PriceHistory.is_current == True
            )
        ).order_by(PriceHistory.trade_date)
        
        result = await self.db.execute(stmt)
        prices = result.scalars().all()
        
        logger.debug(
            f"Fetched {len(prices)} prices for asset {asset_id} "
            f"from {start_date} to {end_date}"
        )
        
        return list(prices)
    
    def _fetch_prices_sync(
        self,
        asset_id: int,
        start_date: date,
        end_date: date
    ) -> List[PriceHistory]:
        """Fetch price history using sync SQLAlchemy.
        
        Args:
            asset_id: Asset identifier
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of PriceHistory records
        """
        prices = self.db.query(PriceHistory).filter(
            PriceHistory.asset_id == asset_id,
            PriceHistory.trade_date >= start_date,
            PriceHistory.trade_date <= end_date,
            PriceHistory.is_current == True
        ).order_by(PriceHistory.trade_date).all()
        
        logger.debug(
            f"Fetched {len(prices)} prices for asset {asset_id} "
            f"from {start_date} to {end_date}"
        )
        
        return prices
    
    async def calculate_risk_metrics(
        self,
        asset_id: int,
        benchmark_id: int,
        lookback_days: int = 365
    ) -> RiskMetrics:
        """Calculate risk metrics for an asset vs benchmark (async).
        
        Fetches historical prices, transforms to weekly log returns,
        and computes Beta and VaR metrics.
        
        Args:
            asset_id: Asset to analyze
            benchmark_id: Benchmark asset (e.g., LASI index proxy)
            lookback_days: Historical period in days (default: 365)
            
        Returns:
            RiskMetrics with beta, VaR, and metadata
            
        Raises:
            RiskCalculationError: If data is insufficient or calculation fails
        """
        logger.info(
            f"Calculating risk metrics: asset={asset_id}, "
            f"benchmark={benchmark_id}, lookback={lookback_days} days"
        )
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Fetch prices for both asset and benchmark
        asset_prices = await self._fetch_prices_async(asset_id, start_date, end_date)
        benchmark_prices = await self._fetch_prices_async(benchmark_id, start_date, end_date)
        
        # Validate data availability
        self._validate_price_data(asset_prices, benchmark_prices, asset_id, benchmark_id)
        
        # Convert to DataFrames
        asset_df = convert_prices_to_dataframe(asset_prices)
        benchmark_df = convert_prices_to_dataframe(benchmark_prices)
        
        # Prepare returns
        asset_returns, benchmark_returns = prepare_returns_data(
            asset_df, benchmark_df, resample_freq="W"
        )
        
        # Validate sufficient observations
        if len(asset_returns) < 10:
            raise RiskCalculationError(
                f"Insufficient weekly observations: {len(asset_returns)} "
                f"(minimum 10 required for reliable metrics)",
                "INSUFFICIENT_OBSERVATIONS"
            )
        
        # Calculate metrics
        beta = calculate_beta(asset_returns, benchmark_returns)
        var_95 = calculate_var_95(asset_returns)
        
        metrics = RiskMetrics(
            beta=round(beta, 4),
            var_95=round(var_95, 4),
            observation_count=len(asset_returns),
            calculation_date=datetime.now(tz=None),
            asset_id=asset_id,
            benchmark_id=benchmark_id,
            lookback_days=lookback_days
        )
        
        logger.info(
            f"Risk metrics calculated: beta={metrics.beta}, "
            f"VaR(95%)={metrics.var_95}%, observations={metrics.observation_count}"
        )
        
        return metrics
    
    def calculate_risk_metrics_sync(
        self,
        asset_id: int,
        benchmark_id: int,
        lookback_days: int = 365
    ) -> RiskMetrics:
        """Calculate risk metrics for an asset vs benchmark (sync version).
        
        Same as calculate_risk_metrics but for synchronous database sessions.
        
        Args:
            asset_id: Asset to analyze
            benchmark_id: Benchmark asset (e.g., LASI index proxy)
            lookback_days: Historical period in days (default: 365)
            
        Returns:
            RiskMetrics with beta, VaR, and metadata
            
        Raises:
            RiskCalculationError: If data is insufficient or calculation fails
        """
        logger.info(
            f"Calculating risk metrics (sync): asset={asset_id}, "
            f"benchmark={benchmark_id}, lookback={lookback_days} days"
        )
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Fetch prices for both asset and benchmark
        asset_prices = self._fetch_prices_sync(asset_id, start_date, end_date)
        benchmark_prices = self._fetch_prices_sync(benchmark_id, start_date, end_date)
        
        # Validate data availability
        self._validate_price_data(asset_prices, benchmark_prices, asset_id, benchmark_id)
        
        # Convert to DataFrames
        asset_df = convert_prices_to_dataframe(asset_prices)
        benchmark_df = convert_prices_to_dataframe(benchmark_prices)
        
        # Prepare returns
        asset_returns, benchmark_returns = prepare_returns_data(
            asset_df, benchmark_df, resample_freq="W"
        )
        
        # Validate sufficient observations
        if len(asset_returns) < 10:
            raise RiskCalculationError(
                f"Insufficient weekly observations: {len(asset_returns)} "
                f"(minimum 10 required for reliable metrics)",
                "INSUFFICIENT_OBSERVATIONS"
            )
        
        # Calculate metrics
        beta = calculate_beta(asset_returns, benchmark_returns)
        var_95 = calculate_var_95(asset_returns)
        
        metrics = RiskMetrics(
            beta=round(beta, 4),
            var_95=round(var_95, 4),
            observation_count=len(asset_returns),
            calculation_date=datetime.now(tz=None),
            asset_id=asset_id,
            benchmark_id=benchmark_id,
            lookback_days=lookback_days
        )
        
        logger.info(
            f"Risk metrics calculated: beta={metrics.beta}, "
            f"VaR(95%)={metrics.var_95}%, observations={metrics.observation_count}"
        )
        
        return metrics
    
    def _validate_price_data(
        self,
        asset_prices: List[PriceHistory],
        benchmark_prices: List[PriceHistory],
        asset_id: int,
        benchmark_id: int
    ) -> None:
        """Validate that sufficient price data exists.
        
        Args:
            asset_prices: Asset price records
            benchmark_prices: Benchmark price records
            asset_id: Asset identifier
            benchmark_id: Benchmark identifier
            
        Raises:
            RiskCalculationError: If data is missing or insufficient
        """
        if not asset_prices:
            raise RiskCalculationError(
                f"No price data found for asset {asset_id}",
                "NO_ASSET_DATA"
            )
        
        if not benchmark_prices:
            raise RiskCalculationError(
                f"No price data found for benchmark {benchmark_id}",
                "NO_BENCHMARK_DATA"
            )
        
        # Minimum raw data points (before resampling)
        min_points = 14  # At least 2 weeks of daily data
        
        if len(asset_prices) < min_points:
            raise RiskCalculationError(
                f"Insufficient asset data: {len(asset_prices)} points "
                f"(minimum {min_points} required)",
                "INSUFFICIENT_ASSET_DATA"
            )
        
        if len(benchmark_prices) < min_points:
            raise RiskCalculationError(
                f"Insufficient benchmark data: {len(benchmark_prices)} points "
                f"(minimum {min_points} required)",
                "INSUFFICIENT_BENCHMARK_DATA"
            )
        
        logger.debug(
            f"Price data validated: asset={len(asset_prices)} points, "
            f"benchmark={len(benchmark_prices)} points"
        )


# ==================== Convenience Functions ====================

async def get_risk_metrics(
    db: AsyncSession,
    asset_id: int,
    benchmark_id: int,
    lookback_days: int = 365
) -> RiskMetrics:
    """Convenience function for async risk metric calculation.
    
    Args:
        db: Async database session
        asset_id: Asset to analyze
        benchmark_id: Benchmark asset
        lookback_days: Lookback period
        
    Returns:
        RiskMetrics object
    """
    engine = RiskEngine(db)
    return await engine.calculate_risk_metrics(asset_id, benchmark_id, lookback_days)


def get_risk_metrics_sync(
    db: Session,
    asset_id: int,
    benchmark_id: int,
    lookback_days: int = 365
) -> RiskMetrics:
    """Convenience function for sync risk metric calculation.
    
    Args:
        db: Database session
        asset_id: Asset to analyze
        benchmark_id: Benchmark asset
        lookback_days: Lookback period
        
    Returns:
        RiskMetrics object
    """
    engine = RiskEngine(db)
    return engine.calculate_risk_metrics_sync(asset_id, benchmark_id, lookback_days)
