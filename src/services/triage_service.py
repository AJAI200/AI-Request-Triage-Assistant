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
    own_session = session is None
    session = session or AsyncSessionLocal()
    triage_repo = triage_repo or get_triage_repository()
    req = None

    try:
        req = await triage_repo.create_request(session, raw_text, process_time_ms=process_time_ms)
        await session.commit()
        await session.refresh(req)

        # AI pipeline calls
        classification = await classify_and_route(raw_text)
        draft = await draft_response(raw_text, classification)

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
            "process_time_ms": process_time_ms,
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

async def get_triage_by_id(
    request_id: int,
    session: Optional[AsyncSession] = None,
    triage_repo: Optional[TriageRepository] = None
) -> Optional[dict]:
    logger.debug("Entering get_triage_by_id")
    own_session = session is None
    session = session or AsyncSessionLocal()
    triage_repo = triage_repo or get_triage_repository()

    try:
        req = await triage_repo.get_by_id(session, request_id)
        if not req:
            logger.debug("Exiting get_triage_by_id with None")
            return None

        if req.status == "needs_review":
            logger.debug("Exiting get_triage_by_id with status needs_review")
            return {
                "id": req.id,
                "status": "needs_review",
                "raw_text": req.raw_text,
                "message": "Could not automatically classify this request. Please review manually.",
                "process_time_ms": req.process_time_ms
            }

        class_obj = req.classification
        draft_obj = req.draft

        logger.debug("Exiting get_triage_by_id successfully")
        return {
            "id": req.id,
            "status": req.status,
            "raw_text": req.raw_text,
            "summary": class_obj.summary if class_obj else None,
            "category": class_obj.category.name if (class_obj and class_obj.category) else "Other",
            "priority": class_obj.priority if class_obj else None,
            "priority_reason": class_obj.priority_reason if class_obj else None,
            "owner": class_obj.owner.name if (class_obj and class_obj.owner) else "Client Success",
            "draft_response": draft_obj.draft_text if draft_obj else None,
            "process_time_ms": req.process_time_ms
        }
    finally:
        if own_session:
            await session.close()

async def list_triaged_requests(
    limit: int = 50,
    session: Optional[AsyncSession] = None,
    triage_repo: Optional[TriageRepository] = None
) -> List[dict]:
    logger.debug("Entering list_triaged_requests")
    own_session = session is None
    session = session or AsyncSessionLocal()
    triage_repo = triage_repo or get_triage_repository()

    try:
        requests = await triage_repo.list_recent(session, limit=limit)
        results = []
        for req in requests:
            if req.status == "needs_review":
                results.append({
                    "id": req.id,
                    "status": "needs_review",
                    "raw_text": req.raw_text,
                    "message": "Could not automatically classify this request. Please review manually.",
                    "process_time_ms": req.process_time_ms
                })
            else:
                class_obj = req.classification
                draft_obj = req.draft
                results.append({
                    "id": req.id,
                    "status": req.status,
                    "raw_text": req.raw_text,
                    "summary": class_obj.summary if class_obj else None,
                    "category": class_obj.category.name if (class_obj and class_obj.category) else "Other",
                    "priority": class_obj.priority if class_obj else None,
                    "priority_reason": class_obj.priority_reason if class_obj else None,
                    "owner": class_obj.owner.name if (class_obj and class_obj.owner) else "Client Success",
                    "draft_response": draft_obj.draft_text if draft_obj else None,
                    "process_time_ms": req.process_time_ms
                })
        logger.debug(f"Exiting list_triaged_requests with {len(results)} items")
        return results
    finally:
        if own_session:
            await session.close()
