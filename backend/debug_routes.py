import sys
import os
sys.path.append(os.getcwd())

from app.main import app
from fastapi.routing import APIRoute

print("DEBUG: Printing all registered routes:")
for route in app.routes:
    if isinstance(route, APIRoute):
        print(f"Path: {route.path} | Name: {route.name} | Methods: {route.methods}")
