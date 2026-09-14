import logging
from typing import Optional, Union
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.base import get_async_db
from src.utils.exceptions.database import DatabaseError

logger = logging.getLogger("triage_assistant.user_repository")

class UserRepository:
    """
    Repository layer encapsulating database query execution for User authentication.
    Supports constructor dependency injection of AsyncSession.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    def _resolve_session(self, session: Optional[AsyncSession]) -> AsyncSession:
        active_session = session or self.session
        if active_session is None:
            raise ValueError("AsyncSession must be provided to UserRepository constructor or method.")
        return active_session

    async def get_by_username(
        self,
        session: Union[AsyncSession, str],
        username: Optional[str] = None
    ) -> Optional[User]:
        logger.debug("Entering UserRepository.get_by_username")
        if isinstance(session, str):
            username = session
            session = None
        db = self._resolve_session(session)
        try:
            stmt = select(User).where(User.username == username)
            res = await db.execute(stmt)
            user = res.scalar_one_or_none()
            logger.debug("Exiting UserRepository.get_by_username")
            return user
        except SQLAlchemyError as exc:
            logger.error(f"Database error in UserRepository.get_by_username for username '{username}': {exc}", exc_info=True)
            raise DatabaseError(f"Failed to fetch user '{username}' from database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in UserRepository.get_by_username: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected repository error fetching user '{username}'") from exc

    async def create_user(
        self,
        session: Union[AsyncSession, str],
        username: str,
        hashed_password: Optional[str] = None,
        role: str = "staff"
    ) -> User:
        logger.debug("Entering UserRepository.create_user")
        if isinstance(session, str):
            role = hashed_password or "staff"
            hashed_password = username
            username = session
            session = None
        db = self._resolve_session(session)
        try:
            user = User(username=username, hashed_password=hashed_password, role=role)
            db.add(user)
            logger.debug("Exiting UserRepository.create_user")
            return user
        except SQLAlchemyError as exc:
            logger.error(f"Database error in UserRepository.create_user for username '{username}': {exc}", exc_info=True)
            raise DatabaseError(f"Failed to create user '{username}' in database") from exc
        except Exception as exc:
            logger.error(f"Unexpected error in UserRepository.create_user: {exc}", exc_info=True)
            raise DatabaseError(f"Unexpected repository error creating user '{username}'") from exc

def get_user_repository(session: Optional[AsyncSession] = Depends(get_async_db)) -> UserRepository:
    return UserRepository(session=session)


