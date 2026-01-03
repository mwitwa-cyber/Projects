"""Risk metrics model for storing calculated risk data."""

from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel, TimestampMixin


class RiskMetricsHistory(BaseModel, TimestampMixin):
    """Stores historical risk metrics calculations.
    
    Designed for TimescaleDB hypertable optimization.
    Each record represents a risk calculation snapshot.
    """
    
    __tablename__ = "risk_metrics"
    
    # Foreign Keys
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    benchmark_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    
    # Calculation Timestamp (primary time dimension for TimescaleDB)
    calculation_date = Column(DateTime, nullable=False, index=True, server_default=func.now())
    
    # Risk Metrics
    beta = Column(Float, nullable=False)
    var_95 = Column(Float, nullable=False)  # Value at Risk (95%) as percentage
    var_99 = Column(Float, nullable=True)   # Value at Risk (99%) as percentage
    
    # Additional Risk Metrics (optional)
    volatility = Column(Float, nullable=True)  # Annualized volatility
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    
    # Calculation Metadata
    observation_count = Column(Integer, nullable=False)
    lookback_days = Column(Integer, nullable=False)
    calculation_status = Column(String(20), nullable=False, default="completed")
    error_message = Column(String(500), nullable=True)
    
    # Relationships
    asset = relationship("Asset", foreign_keys=[asset_id], backref="risk_metrics")
    benchmark = relationship("Asset", foreign_keys=[benchmark_id])
    
    __table_args__ = (
        Index('ix_risk_metrics_asset_date', 'asset_id', 'calculation_date'),
        Index('ix_risk_metrics_benchmark_date', 'benchmark_id', 'calculation_date'),
    )
    
    def __repr__(self):
        return (
            f"<RiskMetrics asset={self.asset_id} "
            f"beta={self.beta:.2f} VaR={self.var_95:.2f}% "
            f"@ {self.calculation_date}>"
        )
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "asset_id": self.asset_id,
            "benchmark_id": self.benchmark_id,
            "calculation_date": self.calculation_date.isoformat() if self.calculation_date else None,
            "beta": self.beta,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "observation_count": self.observation_count,
            "lookback_days": self.lookback_days,
            "calculation_status": self.calculation_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
