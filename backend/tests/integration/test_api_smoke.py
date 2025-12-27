"""
API endpoint smoke tests for frontend-backend integration.
"""
import requests
import pytest

BASE_URL = "http://localhost:8000/api/v1"

@pytest.mark.smoke
def test_optimization_endpoint():
    # Minimal valid payload for optimization
    payload = {"portfolio_id": 1, "objective": "max_sharpe"}
    resp = requests.post(f"{BASE_URL}/optimization/optimize", json=payload)
    assert resp.status_code in (200, 400)  # 400 if portfolio doesn't exist

@pytest.mark.smoke
def test_bond_valuation_endpoint():
    payload = {"coupon_rate": 0.12, "maturity": "2030-12-31", "ytm": 0.15, "face_value": 1000}
    resp = requests.post(f"{BASE_URL}/valuation/bond/price", json=payload)
    assert resp.status_code in (200, 400)

@pytest.mark.smoke
def test_portfolio_crud_endpoints():
    # Create
    payload = {"name": "SmokeTest", "description": "", "portfolio_type": "personal", "holdings": []}
    resp = requests.post(f"{BASE_URL}/portfolios/", json=payload)
    assert resp.status_code in (200, 400)
    if resp.status_code == 200:
        pid = resp.json()["id"]
        # Get
        resp2 = requests.get(f"{BASE_URL}/portfolios/{pid}")
        assert resp2.status_code == 200
        # Delete (if supported)
        requests.delete(f"{BASE_URL}/portfolios/{pid}")

@pytest.mark.smoke
def test_market_data_endpoint():
    resp = requests.get(f"{BASE_URL}/market-data/luse/latest")
    assert resp.status_code in (200, 404)
