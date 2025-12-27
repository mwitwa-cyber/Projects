"""Yield curve data model."""

from sqlalchemy import Column, Integer, Float, Date, String, Index

from app.models.base import BaseModel, TimestampMixin


class YieldCurveData(BaseModel, TimestampMixin):
    """GRZ bond and T-bill yield curve data."""
    
    __tablename__ = "yield_curve_data"
    
    observation_date = Column(Date, nullable=False, index=True)
    
    # Instrument details
    instrument_type = Column(String(50), nullable=False)
    tenor_days = Column(Integer, nullable=False)
    
    # Rates
    yield_rate = Column(Float, nullable=False)
    discount_rate = Column(Float, nullable=True)
    
    # Bond specifics
    coupon_rate = Column(Float, nullable=True)
    face_value = Column(Float, default=100.0)
    
    __table_args__ = (
        Index('ix_yield_curve_date_tenor', 'observation_date', 'tenor_days'),
    )
    
    def __repr__(self):
        return f"<YieldCurve {self.observation_date} {self.tenor_days}d: {self.yield_rate}%>"
