import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db
from src.services.auth_service import create_access_token, decode_access_token
from src.utils.exceptions.auth import AuthenticationError

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()

client = TestClient(app)

def test_login_success():
    response = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"

def test_login_invalid_password():
    response = client.post("/auth/login", json={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 401

def test_login_nonexistent_user():
    response = client.post("/auth/login", json={"username": "nonexistent_user", "password": "password123"})
    assert response.status_code == 401

def test_bearer_token_authentication_success():
    login_res = client.post("/auth/login", json={"username": "admin", "password": "password123"})
    token = login_res.json()["access_token"]

    response = client.get("/triage", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert "X-Process-Time" in response.headers

def test_bearer_token_authentication_invalid():
    response = client.get("/triage", headers={"Authorization": "Bearer invalid_token_123"})
    assert response.status_code == 401
    assert "X-Process-Time" in response.headers

def test_invalid_api_key_header():
    response = client.get("/triage", headers={"X-API-Key": "invalid_secret_key"})
    assert response.status_code == 401
    assert "X-Process-Time" in response.headers

def test_jwt_encode_decode():
    token = create_access_token(user_id=1, username="testuser", role="admin")
    decoded = decode_access_token(token)
    assert decoded["username"] == "testuser"
    assert decoded["role"] == "admin"

def test_decode_invalid_token():
    with pytest.raises(AuthenticationError):
        decode_access_token("invalid.jwt.token")

@pytest.mark.asyncio
async def test_auth_service_verify_password_exception():
    from src.services.auth_service import verify_password, authenticate_user, hash_password
    hashed = hash_password("my_secret_pass")
    assert hashed != "my_secret_pass"
    assert verify_password("my_secret_pass", hashed) is True
    assert verify_password("secret", "invalid_bcrypt_hash_string") is False

    # Test authenticate_user with invalid credentials and own session
    with pytest.raises(AuthenticationError):
        await authenticate_user("admin", "invalid_password")

    result = await authenticate_user("admin", "password123")
    assert result["user"]["username"] == "admin"
