
import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_report_generation():
    # 1. Login
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "totp_api_user", # Use existing user from previous test or register new
            "password": "password123"
        })
        
        if resp.status_code != 200:
            # Try registering
            requests.post(f"{BASE_URL}/auth/register", json={
                "username": "report_user",
                "email": "report@test.com",
                "password": "password123"
            })
            resp = requests.post(f"{BASE_URL}/auth/login", json={
                "username": "report_user",
                "password": "password123"
            })
            
        if resp.status_code != 200:
            print("Login failed")
            sys.exit(1)
            
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Report
        print("Requesting PDF Report...")
        resp = requests.get(f"{BASE_URL}/reports/market-summary", headers=headers)
        
        if resp.status_code == 200:
            content_type = resp.headers.get("content-type")
            if "application/pdf" in content_type:
                print(f"SUCCESS: Received PDF ({len(resp.content)} bytes).")
                with open("market_summary.pdf", "wb") as f:
                    f.write(resp.content)
            else:
                 print(f"FAILED: Content-Type is {content_type}")
                 sys.exit(1)
        else:
            print(f"FAILED: {resp.status_code} {resp.text}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_report_generation()
