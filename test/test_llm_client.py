import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from src.agents.llm_client import call_llm, _call_rest, _call_sdk
from src.utils.exceptions import LLMClientError
from src.settings import settings

@pytest.mark.asyncio
async def test_call_llm_missing_api_key():
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with pytest.raises(LLMClientError, match="GEMINI_API_KEY is not set"):
            await call_llm("test prompt")

@pytest.mark.asyncio
async def test_call_rest_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "REST response"}]}}]
    }

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await _call_rest("prompt", "gemini-flash-lite-latest", "fake_key")
        assert result == "REST response"

@pytest.mark.asyncio
async def test_call_rest_status_error():
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Error"
    mock_response.request = httpx.Request("POST", "http://test")

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(httpx.HTTPStatusError):
            await _call_rest("prompt", "gemini-flash-lite-latest", "fake_key")

@pytest.mark.asyncio
async def test_call_llm_retry_on_transient_error():
    # Simulate a transient 429 error followed by a success on second attempt
    mock_sdk = AsyncMock(side_effect=[
        RuntimeError("429 RESOURCE_EXHAUSTED"),
        "Retried Success Response"
    ])

    with patch("src.agents.llm_client._call_sdk", mock_sdk):
        result = await call_llm("prompt", retries=2, delay=0.1)
        assert result == "Retried Success Response"

@pytest.mark.asyncio
async def test_call_rest_malformed_shape():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"candidates": []}

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(LLMClientError, match="Malformed Gemini REST response"):
            await _call_rest("prompt", "gemini-flash-lite-latest", "fake_key")

@pytest.mark.asyncio
async def test_call_sdk_empty_response():
    mock_client_instance = MagicMock()
    mock_client_instance.models.generate_content.return_value = MagicMock(text="")
    
    with patch("google.genai.Client", return_value=mock_client_instance):
        with pytest.raises(LLMClientError, match="Empty response returned by Gemini SDK"):
            await _call_sdk("prompt", "gemini-flash-lite-latest", "fake_key")

@pytest.mark.asyncio
async def test_call_llm_sdk_fallback_to_rest():
    mock_sdk = AsyncMock(side_effect=RuntimeError("SDK Non-transient Error"))
    mock_rest = AsyncMock(return_value="REST Fallback Response")

    with patch("src.agents.llm_client.HAS_GENAI_SDK", True):
        with patch("src.agents.llm_client._call_sdk", mock_sdk):
            with patch("src.agents.llm_client._call_rest", mock_rest):
                result = await call_llm("prompt", retries=1)
                assert result == "REST Fallback Response"

@pytest.mark.asyncio
async def test_call_llm_retry_exhaustion():
    mock_sdk = AsyncMock(side_effect=RuntimeError("503 UNAVAILABLE"))
    
    with patch("src.agents.llm_client.HAS_GENAI_SDK", True):
        with patch("src.agents.llm_client._call_sdk", mock_sdk):
            with pytest.raises(LLMClientError, match="Failed to obtain LLM response after 2 attempts"):
                await call_llm("prompt", retries=2, delay=0.01)
