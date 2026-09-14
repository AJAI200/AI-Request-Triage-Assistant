from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.llm_client import call_llm
from src.repositories.prompt_repository import get_prompt_repository, PromptRepository
from src.utils.json_parser import parse_llm_json
from src.utils.validators import validate_classification

async def classify_and_route(
    raw_text: str,
    session: Optional[AsyncSession] = None,
    prompt_repo: Optional[PromptRepository] = None
) -> dict:
    prompt_repo = prompt_repo or get_prompt_repository()
    
    if session:
        prompt_template = await prompt_repo.get_active_prompt(session, "CLASSIFY_ROUTE_PROMPT")
    else:
        from src.agents.prompts import CLASSIFY_ROUTE_PROMPT
        prompt_template = CLASSIFY_ROUTE_PROMPT

    prompt = prompt_template.format(text=raw_text)
    llm_res = await call_llm(prompt)
    
    if isinstance(llm_res, dict):
        raw_output = llm_res.get("text", "")
        tokens = {
            "prompt_tokens": llm_res.get("prompt_tokens", 0),
            "completion_tokens": llm_res.get("completion_tokens", 0),
            "total_tokens": llm_res.get("total_tokens", 0)
        }
    else:
        raw_output = str(llm_res)
        tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    result = parse_llm_json(raw_output)
    validate_classification(result)
    result["_tokens"] = tokens
    return result

async def draft_response(
    raw_text: str,
    classification: dict,
    session: Optional[AsyncSession] = None,
    prompt_repo: Optional[PromptRepository] = None
) -> dict:
    prompt_repo = prompt_repo or get_prompt_repository()
    
    if session:
        prompt_template = await prompt_repo.get_active_prompt(session, "DRAFT_RESPONSE_PROMPT")
    else:
        from src.agents.prompts import DRAFT_RESPONSE_PROMPT
        prompt_template = DRAFT_RESPONSE_PROMPT

    prompt = prompt_template.format(
        text=raw_text,
        category=classification.get("category", "Other"),
        priority=classification.get("priority", "Medium"),
        priority_reason=classification.get("priority_reason", ""),
        owner=classification.get("owner", "Client Success"),
        summary=classification.get("summary", ""),
    )
    llm_res = await call_llm(prompt)

    if isinstance(llm_res, dict):
        raw_output = llm_res.get("text", "")
        tokens = {
            "prompt_tokens": llm_res.get("prompt_tokens", 0),
            "completion_tokens": llm_res.get("completion_tokens", 0),
            "total_tokens": llm_res.get("total_tokens", 0)
        }
    else:
        raw_output = str(llm_res)
        tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    result = parse_llm_json(raw_output)
    if not isinstance(result, dict) or "draft_response" not in result:
        raise ValueError("Invalid draft response structure from LLM")
    
    result["_tokens"] = tokens
    return result
