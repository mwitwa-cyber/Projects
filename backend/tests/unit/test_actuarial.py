import pytest
from app.services.actuarial.cm1_valuation import BondPricer, TimeValueOfMoney, AnnuityCalculator
from app.services.actuarial.cm2_portfolio import PortfolioOptimizer
import pandas as pd
import numpy as np

# CM1 Tests
def test_time_value_of_money():
    # v = 1/(1+i)
    assert round(TimeValueOfMoney.discount_factor(0.05, 1), 5) == 0.95238
    # (1+i)^n
    assert round(TimeValueOfMoney.accumulation_factor(0.05, 1), 5) == 1.05000

def test_bond_pricing():
    # Zero coupon bond
    price = BondPricer.price(face_value=100, coupon_rate=0, yield_rate=0.05, years=1)
    # Price should be 100 * v = 95.238
    assert round(price, 2) == 95.18 # Semi-annual by default? 
    # v_semi = 1 / (1 + 0.05/2)^2 = 1 / (1.025)^2 = 1 / 1.050625 = 0.9518...
    # Wait, lets check default freq. frequency=2.
    
    # 5% coupon, 5% yield, Par value
    price_par = BondPricer.price(100, 0.05, 0.05, 5)
    assert round(price_par, 2) == 100.00

def test_annuities():
    # a_n at 0% interest is n
    assert AnnuityCalculator.annuity_immediate(0, 10) == 10.0

# CM2 Tests
def test_portfolio_optimizer():
    returns_diverse = pd.DataFrame({
        "A": [0.1, 0.12, 0.13, 0.09],
        "B": [0.05, 0.06, 0.05, 0.04]
    })
    optimizer = PortfolioOptimizer(returns_diverse, risk_free_rate=0.02)
    metrics = optimizer.max_sharpe_ratio()
    
    assert sum(metrics.weights.values()) == pytest.approx(1.0)
    assert metrics.sharpe_ratio > 0
