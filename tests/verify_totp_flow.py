
import requests
import pyotp
import sys

BASE_URL = "http://localhost:8000/api/v1/auth"
USERNAME = "totp_api_user"
PASSWORD = "password123"
EMAIL = "totp_api@test.com"

session = requests.Session()

def register_and_login():
    print(f"1. Registering/Login user {USERNAME}...")
    # Try register
    try:
        resp = session.post(f"{BASE_URL}/register", json={
            "username": USERNAME,
            "email": EMAIL,
            "password": PASSWORD
        })
        if resp.status_code == 200:
            print("   Registered successfully.")
        else:
            print(f"   Registration status: {resp.status_code} (User likely exists)")
    except Exception as e:
        print(f"   Registration error: {e}")

    # Login to get initial token
    print("2. Logging in to get access token...")
    resp = session.post(f"{BASE_URL}/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if resp.status_code != 200:
        print(f"   Login failed: {resp.text}")
        sys.exit(1)
        
    data = resp.json()
    token = data["access_token"]
    print("   Login successful. Token obtained.")
    return token

def setup_totp(token):
    print("3. Setting up TOTP...")
    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(f"{BASE_URL}/totp/setup", headers=headers)
    
    if resp.status_code != 200:
        print(f"   Setup failed: {resp.text}")
        # If already enabled, we might need a fresh user or disable endpoint
        if "already enabled" in resp.text:
             print("   TOTP already enabled. Proceeding to verify/login tests.")
             # We don't have the secret if already enabled... so this test might fail if we don't know the secret.
             # Ideally we should use a random user each time.
             return None
        sys.exit(1)
        
    data = resp.json()
    secret = data["secret"]
    print(f"   Setup successful. Secret: {secret}")
    return secret

def verify_totp(token, secret):
    if not secret:
        return
        
    print("4. Verifying TOTP...")
    totp = pyotp.TOTP(secret)
    code = totp.now()
    
    headers = {"Authorization": f"Bearer {token}"}
    resp = session.post(f"{BASE_URL}/totp/verify", json={"code": code}, headers=headers)
    
    if resp.status_code == 200:
        print("   Verification successful. TOTP Enabled.")
    else:
        print(f"   Verification failed: {resp.text}")
        sys.exit(1)

def test_login_challenge(secret):
    print("5. Testing Login Challenge...")
    # Login without code
    resp = session.post(f"{BASE_URL}/login", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if resp.status_code == 401 and "TOTP code required" in resp.text:
        print("   Correctly rejected login without code (401 TOTP Required).")
    else:
        print(f"   Unexpected response: {resp.status_code} {resp.text}")
        sys.exit(1)
        
    # Login with code
    print("6. Testing Login with TOTP Code...")
    # Since we might not have the secret if skipped setup, we can only do this if we have secret.
    if secret:
        totp = pyotp.TOTP(secret)
        code = totp.now()
        
        resp = session.post(f"{BASE_URL}/login", json={
            "username": USERNAME,
            "password": PASSWORD,
            "totp_code": code
        })
        
        if resp.status_code == 200:
            print("   Login with code successful!")
        else:
            print(f"   Login with code failed: {resp.text}")
            sys.exit(1)
    else:
        print("   Skipping Login test as secret is unknown.")

if __name__ == "__main__":
    # Use a random suffix to ensure fresh user for reliable test
    import random
    suffix = random.randint(1000, 9999)
    USERNAME = f"totp_api_{suffix}"
    EMAIL = f"totp_{suffix}@test.com"
    
    token = register_and_login()
    secret = setup_totp(token)
    verify_totp(token, secret)
    test_login_challenge(secret)
