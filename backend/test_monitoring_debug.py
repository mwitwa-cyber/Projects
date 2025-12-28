import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("Checking OpenAPI schema...")
try:
    resp = requests.get("http://127.0.0.1:8000/openapi.json")
    schema = resp.json()
    paths = schema.get("paths", {}).keys()
    print(f"Found paths matching 'health': {[p for p in paths if 'health' in p]}")
except Exception as e:
    print(f"Failed to fetch schema: {e}")

print(f"\nRequesting {BASE_URL}/health/detailed ...")
try:
    resp = requests.get(f"{BASE_URL}/health/detailed")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
