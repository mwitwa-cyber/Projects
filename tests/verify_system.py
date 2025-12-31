
import requests
import sys
import json
from datetime import date

BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "test_sys_user"
PASSWORD = "password123"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def verify_system():
    session = requests.Session()
    token = None
    
    # 1. Health Check
    try:
        resp = session.get(f"http://localhost:8000/health")
        if resp.status_code == 200:
            log("Health Check Passed", "SUCCESS")
        else:
            log(f"Health Check Failed: {resp.status_code}", "ERROR")
    except Exception as e:
        log(f"Health Check Connection Failed: {e}", "ERROR")
        sys.exit(1)

    # 2. Authentication (Register/Login)
    log("Testing Authentication...")
    try:
        # Try Login
        resp = session.post(f"{BASE_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
        
        if resp.status_code == 401: # Maybe user doesn't exist
            log("User not found, registering...", "INFO")
            reg = session.post(f"{BASE_URL}/auth/register", json={
                "username": USERNAME, "email": "sys_test@luse.co.zm", "password": PASSWORD
            })
            if reg.status_code in [200, 201]:
                log("Registration Successful", "SUCCESS")
                # Login again
                resp = session.post(f"{BASE_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
            else:
                log(f"Registration Failed: {reg.text}", "ERROR")
                sys.exit(1)

        if resp.status_code == 200:
            token = resp.json()["access_token"]
            session.headers.update({"Authorization": f"Bearer {token}"})
            log("Login Successful", "SUCCESS")
        else:
            log(f"Login Failed: {resp.text}", "ERROR")
            sys.exit(1)

    except Exception as e:
        log(f"Auth Exception: {e}", "ERROR")
        sys.exit(1)

    # 3. Market Data (Tiles)
    log("Testing Market Data (Tiles)...")
    try:
        today = date.today().isoformat()
        resp = session.get(f"{BASE_URL}/market-data/market-summary?date={today}")
        if resp.status_code == 200:
            data = resp.json()
            if len(data) > 0:
                log(f"Market Summary Received: {len(data)} tickers", "SUCCESS")
            else:
                log("Market Summary Empty (Check Seeding)", "ERROR")
        else:
            log(f"Market Summary Failed: {resp.status_code}", "ERROR")
    except Exception as e:
        log(f"Market Data Exception: {e}", "ERROR")

    # 4. Analytics: Yield Curve
    log("Testing Analytics (Yield Curve)...")
    try:
        resp = session.get(f"{BASE_URL}/analytics/yield-curve")
        if resp.status_code == 200:
            data = resp.json()
            if "curve_points" in data:
                log("Yield Curve Data Valid", "SUCCESS")
            else:
                log("Yield Curve Data Malformed", "ERROR")
        else:
            log(f"Yield Curve Failed: {resp.status_code}", "ERROR")
    except Exception as e:
        log(f"Yield Curve Exception: {e}", "ERROR")

    # 5. Analytics: CAPM
    log("Testing Analytics (CAPM Code)...")
    try:
        ticker = "ZNCO"
        resp = session.get(f"{BASE_URL}/analytics/capm/{ticker}")
        if resp.status_code == 200:
            data = resp.json()
            if "expected_return" in data:
                log(f"CAPM for {ticker} Valid: E(R)={data['expected_return']:.2%}", "SUCCESS")
            else:
                log("CAPM Data Malformed", "ERROR")
        else:
            log(f"CAPM Failed: {resp.status_code}", "ERROR")
    except Exception as e:
        log(f"CAPM Exception: {e}", "ERROR")

    # 6. Backtesting
    log("Testing Strategy Backtest...")
    try:
        payload = {
            "initial_capital": 10000,
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "weights": {"ZNCO": 0.5, "SCBL": 0.5}
        }
        resp = session.post(f"{BASE_URL}/backtest/run", json=payload)
        if resp.status_code == 200:
            data = resp.json()
            if "metrics" in data:
                log(f"Backtest Successful. CAGR: {data['metrics']['cagr']}", "SUCCESS")
            else:
                log("Backtest Response Malformed", "ERROR")
        else:
            log(f"Backtest Failed: {resp.status_code} {resp.text}", "ERROR")
    except Exception as e:
        log(f"Backtest Exception: {e}", "ERROR")

    # 7. Reporting (PDF)
    log("Testing PDF Generation...")
    try:
        resp = session.get(f"{BASE_URL}/reports/market-summary")
        if resp.status_code == 200:
            if "application/pdf" in resp.headers.get("content-type", ""):
                 log(f"PDF Generated ({len(resp.content)} bytes)", "SUCCESS")
            else:
                 log(f"PDF Content-Type Invalid: {resp.headers.get('content-type')}", "ERROR")
        else:
            log(f"PDF Failed: {resp.status_code}", "ERROR")
    except Exception as e:
        log(f"PDF Exception: {e}", "ERROR")

if __name__ == "__main__":
    verify_system()
