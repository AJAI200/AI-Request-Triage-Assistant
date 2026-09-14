import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from src.main import app
from src.database import init_db
from test.fixtures.mock_requests import MOCK_REQUESTS

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": "node_solutions_secret_key_123"}

def test_post_triage_unauthorized():
    # Calling POST /triage without auth headers returns 401 Unauthorized
    response = client.post("/triage", json={"text": MOCK_REQUESTS[0]["text"]})
    assert response.status_code == 401

def test_post_triage_empty_input():
    response = client.post("/triage", json={"text": "   "}, headers=AUTH_HEADERS)
    assert response.status_code == 400
    assert response.json()["detail"] == "Request text cannot be empty."

def test_post_triage_valid_request():
    mock_text = MOCK_REQUESTS[2]["text"]  # Invoice request
    response = client.post("/triage", json={"text": mock_text}, headers=AUTH_HEADERS)
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["status"] in ["classified", "needs_review"]
    assert "id" in data

