from src.agents.llm_client import call_llm
from src.agents.prompts import CLASSIFY_ROUTE_PROMPT, DRAFT_RESPONSE_PROMPT
from src.utils.json_parser import parse_llm_json
from src.utils.validators import validate_classification

async def classify_and_route(raw_text: str) -> dict:
    prompt = CLASSIFY_ROUTE_PROMPT.format(text=raw_text)
    raw_output = await call_llm(prompt)
    result = parse_llm_json(raw_output)
    validate_classification(result)
    return result

async def draft_response(raw_text: str, classification: dict) -> dict:
    prompt = DRAFT_RESPONSE_PROMPT.format(
        text=raw_text,
        category=classification.get("category", "Other"),
        priority=classification.get("priority", "Medium"),
        priority_reason=classification.get("priority_reason", ""),
        owner=classification.get("owner", "Client Success"),
        summary=classification.get("summary", ""),
    )
    raw_output = await call_llm(prompt)
    result = parse_llm_json(raw_output)
    if not isinstance(result, dict) or "draft_response" not in result:
        raise ValueError("Invalid draft response structure from LLM")
    return result
