import time
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.triage_agent import classify_and_route, draft_response
from src.repositories.triage_repository import TriageRepository, get_triage_repository
from src.models.base import AsyncSessionLocal
from src.utils.exceptions import JSONParseError, ValidationError, LLMClientError
from src.utils.lookups import lookup_category_id, lookup_owner_id
from src.utils.error_logger import log_error_to_db

logger = logging.getLogger("triage_assistant.triage_service")

async def run_triage(
    raw_text: str,
    session: Optional[AsyncSession] = None,
    triage_repo: Optional[TriageRepository] = None,
    process_time_ms: Optional[float] = None
) -> dict:
    logger.debug("Entering run_triage")
    start_time = time.time()
    own_session = session is None
    session = session or AsyncSessionLocal()
    triage_repo = triage_repo or get_triage_repository()
    req = None

    try:
        req = await triage_repo.create_request(session, raw_text, process_time_ms=process_time_ms)
        await session.commit()
        await session.refresh(req)

        # AI pipeline calls with dynamic prompt repository lookup
        classification = await classify_and_route(raw_text, session=session)
        draft = await draft_response(raw_text, classification, session=session)

        # Aggregate token usage across pipeline steps
        c_tok = classification.get("_tokens", {})
        d_tok = draft.get("_tokens", {})
        prompt_tokens = c_tok.get("prompt_tokens", 0) + d_tok.get("prompt_tokens", 0)
        completion_tokens = c_tok.get("completion_tokens", 0) + d_tok.get("completion_tokens", 0)
        total_tokens = c_tok.get("total_tokens", 0) + d_tok.get("total_tokens", 0)

        calc_time = process_time_ms if process_time_ms is not None else round((time.time() - start_time) * 1000, 2)
        await triage_repo.update_tokens(session, req, prompt_tokens, completion_tokens, total_tokens, calc_time)

        # Lookups & storage via Repository Layer
        cat_id = await lookup_category_id(session, classification["category"])
        own_id = await lookup_owner_id(session, classification["owner"])

        await triage_repo.add_classification(
            session=session,
            request_id=req.id,
            summary=classification["summary"],
            category_id=cat_id,
            priority=classification["priority"],
            priority_reason=classification["priority_reason"],
            owner_id=own_id,
        )
        await triage_repo.add_draft(
            session=session,
            request_id=req.id,
            draft_text=draft["draft_response"]
        )
        req.status = "classified"
        await session.commit()

        logger.debug("Exiting run_triage with status classified")
        return {
            "id": req.id,
            "status": "classified",
            "raw_text": raw_text,
            "summary": classification["summary"],
            "category": classification["category"],
            "priority": classification["priority"],
            "priority_reason": classification["priority_reason"],
            "owner": classification["owner"],
            "draft_response": draft["draft_response"],
            "process_time_ms": calc_time,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

    except (JSONParseError, ValidationError, LLMClientError, ValueError) as exc:
        # Graceful degradation for expected LLM output & parsing failures
        await session.rollback()
        await log_error_to_db(exc, session=session, process_time_ms=process_time_ms)
        if req is not None:
            req.status = "needs_review"
            await session.commit()
            logger.debug("Exiting run_triage with status needs_review")
            return {
                "id": req.id,
                "status": "needs_review",
                "raw_text": raw_text,
                "message": "Could not automatically classify this request. Please review manually.",
                "process_time_ms": process_time_ms,
            }
        raise exc

    except Exception as exc:
        # Unexpected infrastructure/programming bug: rollback, log error, and raise 500
        await session.rollback()
        await log_error_to_db(exc, session=session, process_time_ms=process_time_ms)
        raise exc

    finally:
        if own_session:
            await session.close()

async def approve_triage_draft(
    request_id: int,
    final_text: str,
    session: Optional[AsyncSession] = None,
    triage_repo: Optional[TriageRepository] = None
) -> dict:
    own_session = session is None
    session = session or AsyncSessionLocal()
    triage_repo = triage_repo or get_triage_repository()
    try:
        draft = await triage_repo.approve_draft(session, request_id, final_text)
        if not draft:
            raise ValueError(f"Request #{request_id} not found or has no draft.")
        await session.commit()
        return {
            "request_id": request_id,
            "status": "sent",
            "final_text": draft.final_text,
            "sent_at": draft.sent_at.isoformat() if draft.sent_at else None
        }
    finally:
        if own_session:
            await session.close()

