import pytest
from app.services.auth_service import get_password_hash, verify_password, create_access_token
from jose import jwt, JWTError
from app.services.auth_service import SECRET_KEY, ALGORITHM

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_jwt_token_creation():
    data = {"sub": "testuser"}
    token = create_access_token(data)
    
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded
