import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.request import Request
from src.models.classification import Classification
from src.models.response_draft import ResponseDraft

logger = logging.getLogger("triage_assistant.triage_repository")

class TriageRepository:
    """
    Repository layer encapsulating database query execution for Triage requests,
    classifications, and drafts.
    """

    async def create_request(
        self,
        session: AsyncSession,
        raw_text: str,
        process_time_ms: Optional[float] = None
    ) -> Request:
        logger.debug("Entering TriageRepository.create_request")
        req = Request(raw_text=raw_text, status="new", process_time_ms=process_time_ms)
        session.add(req)
        logger.debug("Exiting TriageRepository.create_request")
        return req

    async def add_classification(
        self,
        session: AsyncSession,
        request_id: int,
        summary: str,
        category_id: int,
        priority: str,
        priority_reason: str,
        owner_id: int,
    ) -> Classification:
        logger.debug("Entering TriageRepository.add_classification")
        class_obj = Classification(
            request_id=request_id,
            summary=summary,
            category_id=category_id,
            priority=priority,
            priority_reason=priority_reason,
            owner_id=owner_id,
        )
        session.add(class_obj)
        logger.debug("Exiting TriageRepository.add_classification")
        return class_obj

    async def add_draft(
        self,
        session: AsyncSession,
        request_id: int,
        draft_text: str
    ) -> ResponseDraft:
        logger.debug("Entering TriageRepository.add_draft")
        draft_obj = ResponseDraft(request_id=request_id, draft_text=draft_text)
        session.add(draft_obj)
        logger.debug("Exiting TriageRepository.add_draft")
        return draft_obj

    async def get_by_id(self, session: AsyncSession, request_id: int) -> Optional[Request]:
        logger.debug("Entering TriageRepository.get_by_id")
        stmt = (
            select(Request)
            .where(Request.id == request_id)
            .options(
                selectinload(Request.classification).selectinload(Classification.category),
                selectinload(Request.classification).selectinload(Classification.owner),
                selectinload(Request.draft)
            )
        )
        res = await session.execute(stmt)
        req = res.scalar_one_or_none()
        logger.debug("Exiting TriageRepository.get_by_id")
        return req

    async def list_recent(self, session: AsyncSession, limit: int = 50) -> List[Request]:
        logger.debug("Entering TriageRepository.list_recent")
        stmt = (
            select(Request)
            .order_by(Request.id.desc())
            .limit(limit)
            .options(
                selectinload(Request.classification).selectinload(Classification.category),
                selectinload(Request.classification).selectinload(Classification.owner),
                selectinload(Request.draft)
            )
        )
        res = await session.execute(stmt)
        requests = res.scalars().all()
        logger.debug("Exiting TriageRepository.list_recent")
        return requests

def get_triage_repository() -> TriageRepository:
    return TriageRepository()
