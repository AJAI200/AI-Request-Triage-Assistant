import pytest
import pytest_asyncio
from src.database import init_db
from src.services.triage_service import run_triage, get_triage_by_id, list_triaged_requests
from test.fixtures.mock_requests import MOCK_REQUESTS

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()

@pytest.mark.asyncio
async def test_run_triage_service_success():
    mock_text = MOCK_REQUESTS[1]["text"]  # Portal outage
    result = await run_triage(mock_text)
    assert result["status"] in ["classified", "needs_review"]
    assert "id" in result

    # Verify retrieval by ID
    stored = await get_triage_by_id(result["id"])
    assert stored is not None
    assert stored["id"] == result["id"]

@pytest.mark.asyncio
async def test_run_triage_service_needs_review_fallback():
    from unittest.mock import patch
    from src.utils.exceptions import LLMClientError

    with patch("src.services.triage_service.classify_and_route", side_effect=LLMClientError("Simulated LLM Error")):
        result = await run_triage("Some complex ambiguous input text")
        assert result["status"] == "needs_review"
        assert "message" in result
        assert result["id"] is not None

        # Verify retrieval of needs_review request
        stored = await get_triage_by_id(result["id"])
        assert stored["status"] == "needs_review"
        assert stored["message"] == "Could not automatically classify this request. Please review manually."

@pytest.mark.asyncio
async def test_list_triaged_requests():
    results = await list_triaged_requests(limit=10)
    assert isinstance(results, list)
