import logging
from typing import Optional, Union
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.prompt_template import PromptTemplate
from src.models.base import get_async_db
from src.utils.exceptions.database import DatabaseError

logger = logging.getLogger("triage_assistant.prompt_repository")

class PromptRepository:
    """
    Repository layer encapsulating database queries for AI Prompt Templates.
    Supports constructor dependency injection of AsyncSession.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    def _resolve_session(self, session: Optional[AsyncSession]) -> AsyncSession:
        active_session = session or self.session
        if active_session is None:
            raise ValueError("AsyncSession must be provided to PromptRepository constructor or method.")
        return active_session

    async def get_active_prompt(
        self,
        session: Union[AsyncSession, str],
        prompt_name: Optional[str] = None
    ) -> str:
        if isinstance(session, str):
            prompt_name = session
            session = None
        db = self._resolve_session(session)
        logger.debug(f"Entering PromptRepository.get_active_prompt for '{prompt_name}'")
        try:
            stmt = select(PromptTemplate).where(
                PromptTemplate.name == prompt_name,
                PromptTemplate.is_active == True
            ).order_by(PromptTemplate.version.desc())
            
            result = await db.execute(stmt)
            template = result.scalars().first()
            if template and template.template_text:
                logger.debug(f"Exiting PromptRepository.get_active_prompt for '{prompt_name}'")
                return template.template_text

            raise ValueError(f"Active prompt template '{prompt_name}' not found in database.")
        except ValueError:
            raise
        except SQLAlchemyError as exc:
            logger.error(f"Database error in PromptRepository.get_active_prompt for '{prompt_name}': {exc}", exc_info=True)
            raise DatabaseError(f"Failed to fetch active prompt template '{prompt_name}' from database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in PromptRepository.get_active_prompt for '{prompt_name}': {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected error fetching active prompt template '{prompt_name}'") from exc

def get_prompt_repository(session: Optional[AsyncSession] = Depends(get_async_db)) -> PromptRepository:
    return PromptRepository(session=session)


