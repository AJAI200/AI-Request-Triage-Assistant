import asyncio
import httpx
import logging
from src.settings import settings
from src.utils.exceptions import LLMClientError
from src.utils.error_logger import log_error_to_db

logger = logging.getLogger("triage_assistant.llm_client")

# Top-level optional SDK check
try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

async def _call_sdk(prompt: str, model_name: str, api_key: str) -> str:
    logger.debug("Entering _call_sdk")
    client = genai.Client(api_key=api_key)
    response = await asyncio.to_thread(
        client.models.generate_content,
        model=model_name,
        contents=prompt
    )
    if response and response.text:
        logger.debug("Exiting _call_sdk successfully")
        return response.text
    logger.warning("Empty response returned by Gemini SDK")
    logger.debug("Exiting _call_sdk with LLMClientError")
    raise LLMClientError("Empty response returned by Gemini SDK")

async def _call_rest(prompt: str, model_name: str, api_key: str) -> str:
    logger.debug("Entering _call_rest")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(url, json=payload, headers=headers)
        if res.status_code != 200:
            logger.warning(f"Gemini REST returned status {res.status_code}: {res.text}")
            logger.debug("Exiting _call_rest with HTTPStatusError")
            raise httpx.HTTPStatusError(
                f"Gemini REST status {res.status_code}: {res.text}",
                request=res.request,
                response=res
            )
        data = res.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            logger.debug("Exiting _call_rest successfully")
            return text
        except (KeyError, IndexError) as err:
            logger.warning(f"Malformed REST payload shape: {data}")
            logger.debug("Exiting _call_rest with LLMClientError")
            raise LLMClientError(f"Malformed Gemini REST response: {data}") from err

def is_transient_error(exc: Exception) -> bool:
    """
    Determines if an exception is transient (429 rate limit, 5xx server error).
    Checks HTTP status codes, SDK error attributes, and message fallbacks.
    """
    if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
        if exc.response.status_code in {429, 500, 502, 503, 504}:
            return True

    code = getattr(exc, "code", None) or getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if code in {429, 500, 502, 503, 504, "RESOURCE_EXHAUSTED", "UNAVAILABLE"}:
        return True

    err_str = str(exc)
    return any(term in err_str for term in ["429", "503", "500", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "Quota exceeded"])

async def call_llm(prompt: str, retries: int = 3, delay: float = 1.0) -> str:
    """
    Unified LLM caller with top-level SDK import check, REST fallback,
    DB error logging, and single DRY retry backoff loop.
    """
    logger.debug("Entering call_llm")
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        err = LLMClientError("GEMINI_API_KEY is not set in environment settings")
        await log_error_to_db(err)
        logger.debug("Exiting call_llm due to missing GEMINI_API_KEY")
        raise err

    model_name = settings.GEMINI_MODEL or "gemini-flash-lite-latest"
    last_exception = None

    for attempt in range(retries):
        try:
            if HAS_GENAI_SDK:
                res = await _call_sdk(prompt, model_name, api_key)
            else:
                res = await _call_rest(prompt, model_name, api_key)
            logger.debug("Exiting call_llm successfully")
            return res
        except Exception as exc:
            last_exception = exc

            # If SDK call failed for non-transient reasons, try REST fallback
            if HAS_GENAI_SDK and not is_transient_error(exc):
                try:
                    res = await _call_rest(prompt, model_name, api_key)
                    logger.debug("Exiting call_llm via REST fallback successfully")
                    return res
                except Exception as rest_exc:
                    last_exception = rest_exc

            # Handle transient retries
            if is_transient_error(last_exception) and attempt < retries - 1:
                wait_time = delay * (attempt + 1)
                logger.warning(f"Transient LLM error ({last_exception}). Retrying in {wait_time}s... (Attempt {attempt+1}/{retries})")
                await asyncio.sleep(wait_time)
                continue

    final_err = LLMClientError(f"Failed to obtain LLM response after {retries} attempts: {last_exception}")
    await log_error_to_db(final_err)
    logger.debug("Exiting call_llm with final_err")
    raise final_err
