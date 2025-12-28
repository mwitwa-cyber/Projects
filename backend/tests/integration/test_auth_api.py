import pytest
from app.models.user import User

def test_register_user(client, db_session):
    # Ensure clean state
    db_session.query(User).filter(User.username == "newuser").delete()
    db_session.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "newuser", "email": "newuser@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data

def test_login_user(client, db_session):
    # Ensure user exists (depends on register or seed)
    if not db_session.query(User).filter(User.username == "testlogin").first():
        client.post(
            "/api/v1/auth/register",
            json={"username": "testlogin", "email": "login@example.com", "password": "password123"}
        )
    
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "testlogin", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "wrongpassword"}
    )
    assert response.status_code == 401
