"""
Integration tests for end-to-end API workflow and valuation pipeline.
"""
import pytest
import requests

BASE_URL = "http://localhost:8000/api/v1"

@pytest.mark.integration
def test_portfolio_creation_to_optimization():
    # 1. Create portfolio with LUSE securities
    portfolio_data = {
        "name": "Test Portfolio",
        "description": "Integration test portfolio",
        "portfolio_type": "personal",
        "holdings": [
            {"ticker": "ZCCM-IH", "quantity": 100},
            {"ticker": "Zanaco", "quantity": 200}
        ]
    }
    resp = requests.post(f"{BASE_URL}/portfolios/", json=portfolio_data)
    assert resp.status_code == 200
    portfolio = resp.json()
    portfolio_id = portfolio["id"]

    # 2. Fetch live market data
    resp = requests.get(f"{BASE_URL}/market-data/luse/latest")
    assert resp.status_code == 200
    market_data = resp.json()
    assert "lasi_value" in market_data

    # 3. Calculate returns and covariance
    resp = requests.get(f"{BASE_URL}/portfolios/{portfolio_id}/returns")
    assert resp.status_code == 200
    returns = resp.json()
    assert "returns" in returns

    # 4. Run optimization
    opt_data = {"portfolio_id": portfolio_id, "objective": "max_sharpe"}
    resp = requests.post(f"{BASE_URL}/optimization/optimize", json=opt_data)
    assert resp.status_code == 200
    opt_result = resp.json()
    assert "optimal_weights" in opt_result

    # 5. Verify output consistency
    assert abs(sum(opt_result["optimal_weights"].values()) - 1.0) < 1e-6

@pytest.mark.integration
def test_valuation_pipeline():
    # Bond pricing with live yield curve
    bond_data = {
        "coupon_rate": 0.12,
        "maturity": "2030-12-31",
        "ytm": 0.15,
        "face_value": 1000
    }
    resp = requests.post(f"{BASE_URL}/valuation/bond/price", json=bond_data)
    assert resp.status_code == 200
    bond_result = resp.json()
    assert "price" in bond_result

    # DCF with market data
    dcf_data = {
        "cash_flows": [100, 110, 120, 130, 140],
        "growth_rate": 0.05,
        "discount_rate": 0.13
    }
    resp = requests.post(f"{BASE_URL}/valuation/equity/dcf", json=dcf_data)
    assert resp.status_code == 200
    dcf_result = resp.json()
    assert "intrinsic_value" in dcf_result

    # Annuity calculations
    annuity_data = {
        "payment": 1000,
        "interest_rate": 0.1,
        "term": 10
    }
    resp = requests.post(f"{BASE_URL}/valuation/annuity", json=annuity_data)
    assert resp.status_code == 200
    annuity_result = resp.json()
    assert "present_value" in annuity_result
