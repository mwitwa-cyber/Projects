import requests

# Fetch the OpenAPI schema
schema = requests.get('http://localhost:8000/openapi.json').json()

# Print all registered paths
for path in schema['paths']:
    print(path)
