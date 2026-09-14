import datetime
import logging
from typing import List, Optional, Union
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.request import Request
from src.models.classification import Classification
from src.models.response_draft import ResponseDraft
from src.models.base import get_async_db
from src.utils.exceptions.database import DatabaseError

logger = logging.getLogger("triage_assistant.triage_repository")

class TriageRepository:
    """
    Repository layer encapsulating database query execution for Triage requests,
    classifications, and drafts.
    Supports constructor dependency injection of AsyncSession.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    def _resolve_session(self, session: Optional[AsyncSession]) -> AsyncSession:
        active_session = session or self.session
        if active_session is None:
            raise ValueError("AsyncSession must be provided to TriageRepository constructor or method.")
        return active_session

    async def create_request(
        self,
        session: Optional[AsyncSession] = None,
        raw_text: str = "",
        process_time_ms: Optional[float] = None
    ) -> Request:
        if isinstance(session, str):
            process_time_ms = raw_text if isinstance(raw_text, (float, int)) else None
            raw_text = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.create_request")
        try:
            req = Request(raw_text=raw_text, status="new", process_time_ms=process_time_ms)
            db.add(req)
            logger.debug("Exiting TriageRepository.create_request")
            return req
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.create_request: {exc}", exc_info=True)
            raise DatabaseError("Failed to create triage request in database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.create_request: {exc}", exc_info=True)
            raise DatabaseError("Unexpected error creating triage request") from exc

    async def update_tokens(
        self,
        session: Optional[AsyncSession] = None,
        req: Optional[Request] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        process_time_ms: Optional[float] = None
    ) -> None:
        if isinstance(session, Request):
            process_time_ms = total_tokens if isinstance(total_tokens, (float, int)) else None
            total_tokens = completion_tokens
            completion_tokens = prompt_tokens
            prompt_tokens = req if isinstance(req, int) else 0
            req = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.update_tokens")
        try:
            req.prompt_tokens = prompt_tokens
            req.completion_tokens = completion_tokens
            req.total_tokens = total_tokens
            if process_time_ms is not None:
                req.process_time_ms = process_time_ms
            logger.debug("Exiting TriageRepository.update_tokens")
        except Exception as exc:
            logger.error(f"Database error in TriageRepository.update_tokens for request #{getattr(req, 'id', None)}: {exc}", exc_info=True)
            raise DatabaseError(f"Failed to update token metrics for request #{getattr(req, 'id', None)}") from exc

    async def add_classification(
        self,
        session: Optional[AsyncSession] = None,
        request_id: int = 0,
        summary: str = "",
        category_id: int = 0,
        priority: str = "",
        priority_reason: str = "",
        owner_id: int = 0,
    ) -> Classification:
        if isinstance(session, int):
            owner_id = priority_reason if isinstance(priority_reason, int) else owner_id
            priority_reason = priority if isinstance(priority, str) else priority_reason
            priority = category_id if isinstance(category_id, str) else priority
            category_id = summary if isinstance(summary, int) else category_id
            summary = request_id if isinstance(request_id, str) else summary
            request_id = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.add_classification")
        try:
            class_obj = Classification(
                request_id=request_id,
                summary=summary,
                category_id=category_id,
                priority=priority,
                priority_reason=priority_reason,
                owner_id=owner_id,
            )
            db.add(class_obj)
            logger.debug("Exiting TriageRepository.add_classification")
            return class_obj
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.add_classification for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Failed to save classification for request #{request_id}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.add_classification for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected error saving classification for request #{request_id}") from exc

    async def add_draft(
        self,
        session: Optional[AsyncSession] = None,
        request_id: int = 0,
        draft_text: str = ""
    ) -> ResponseDraft:
        if isinstance(session, int):
            draft_text = request_id
            request_id = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.add_draft")
        try:
            draft_obj = ResponseDraft(request_id=request_id, draft_text=draft_text)
            db.add(draft_obj)
            logger.debug("Exiting TriageRepository.add_draft")
            return draft_obj
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.add_draft for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Failed to save draft for request #{request_id}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.add_draft for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected error saving draft for request #{request_id}") from exc

    async def approve_draft(
        self,
        session: Optional[AsyncSession] = None,
        request_id: int = 0,
        final_text: str = ""
    ) -> Optional[ResponseDraft]:
        if isinstance(session, int):
            final_text = request_id
            request_id = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.approve_draft")
        try:
            req = await self.get_by_id(db, request_id)
            if not req or not req.draft:
                return None
            req.draft.final_text = final_text
            req.draft.sent_at = datetime.datetime.now(datetime.timezone.utc)
            req.status = "sent"
            logger.debug("Exiting TriageRepository.approve_draft")
            return req.draft
        except DatabaseError:
            raise
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.approve_draft for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Failed to approve draft for request #{request_id}") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.approve_draft for request #{request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected error approving draft for request #{request_id}") from exc

    async def get_by_id(self, session: Optional[AsyncSession] = None, request_id: int = 0) -> Optional[Request]:
        if isinstance(session, int):
            request_id = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.get_by_id")
        try:
            stmt = (
                select(Request)
                .where(Request.id == request_id)
                .options(
                    selectinload(Request.classification).selectinload(Classification.category),
                    selectinload(Request.classification).selectinload(Classification.owner),
                    selectinload(Request.draft)
                )
            )
            res = await db.execute(stmt)
            req = res.scalar_one_or_none()
            logger.debug("Exiting TriageRepository.get_by_id")
            return req
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.get_by_id for ID {request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Failed to fetch request #{request_id} from database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.get_by_id for ID {request_id}: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected error fetching request #{request_id}") from exc

    async def list_recent(self, session: Optional[AsyncSession] = None, limit: int = 50) -> List[Request]:
        if isinstance(session, int):
            limit = session
            session = None
        db = self._resolve_session(session)
        logger.debug("Entering TriageRepository.list_recent")
        try:
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
            res = await db.execute(stmt)
            requests = res.scalars().all()
            logger.debug("Exiting TriageRepository.list_recent")
            return requests
        except SQLAlchemyError as exc:
            logger.error(f"Database error in TriageRepository.list_recent: {exc}", exc_info=True)
            raise DatabaseError("Failed to list recent requests from database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in TriageRepository.list_recent: {exc}", exc_info=True)
            raise DatabaseError("Unexpected error listing recent requests") from exc

def get_triage_repository(session: Optional[AsyncSession] = Depends(get_async_db)) -> TriageRepository:
    return TriageRepository(session=session)


