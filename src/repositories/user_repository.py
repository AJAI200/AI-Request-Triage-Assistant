import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User

logger = logging.getLogger("triage_assistant.user_repository")

class UserRepository:
    """
    Repository layer encapsulating database query execution for User authentication.
    """

    async def get_by_username(self, session: AsyncSession, username: str) -> Optional[User]:
        logger.debug("Entering UserRepository.get_by_username")
        stmt = select(User).where(User.username == username)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()
        logger.debug("Exiting UserRepository.get_by_username")
        return user

    async def create_user(
        self,
        session: AsyncSession,
        username: str,
        hashed_password: str,
        role: str = "staff"
    ) -> User:
        logger.debug("Entering UserRepository.create_user")
        user = User(username=username, hashed_password=hashed_password, role=role)
        session.add(user)
        logger.debug("Exiting UserRepository.create_user")
        return user

def get_user_repository() -> UserRepository:
    return UserRepository()
