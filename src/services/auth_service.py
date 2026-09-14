import datetime
import logging
from typing import Optional
import jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from src.settings import settings
from src.repositories.user_repository import UserRepository, get_user_repository
from src.utils.exceptions.auth import AuthenticationError
from src.models.base import AsyncSessionLocal

logger = logging.getLogger("triage_assistant.auth_service")

def hash_password(password: str) -> str:
    logger.debug("Entering hash_password")
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
    logger.debug("Exiting hash_password")
    return hashed

def verify_password(plain_password: str, hashed_password: str) -> bool:
    logger.debug("Entering verify_password")
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
        logger.debug("Exiting verify_password")
        return is_valid
    except Exception as exc:
        logger.warning(f"Error verifying password: {exc}")
        logger.debug("Exiting verify_password with False")
        return False

def create_access_token(user_id: int, username: str, role: str) -> str:
    logger.debug("Entering create_access_token")
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug("Exiting create_access_token")
    return token

def decode_access_token(token: str) -> dict:
    logger.debug("Entering decode_access_token")
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        logger.debug("Exiting decode_access_token successfully")
        return payload
    except jwt.PyJWTError as exc:
        logger.warning(f"Failed to decode access token: {exc}")
        logger.debug("Exiting decode_access_token with AuthenticationError")
        raise AuthenticationError("Invalid or expired JWT token") from exc

async def authenticate_user(
    username: str,
    password: str,
    session: Optional[AsyncSession] = None,
    user_repo: Optional[UserRepository] = None
) -> dict:
    logger.debug("Entering authenticate_user")
    own_session = session is None
    session = session or AsyncSessionLocal()
    user_repo = user_repo or get_user_repository()

    try:
        user = await user_repo.get_by_username(session, username)
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed authentication attempt for username: {username}")
            raise AuthenticationError("Invalid username or password")

        token = create_access_token(user.id, user.username, user.role)
        logger.debug("Exiting authenticate_user successfully")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    finally:
        if own_session:
            await session.close()

async def register_user(
    username: str,
    password: str,
    session: Optional[AsyncSession] = None,
    user_repo: Optional[UserRepository] = None
) -> dict:
    logger.debug("Entering register_user")
    own_session = session is None
    session = session or AsyncSessionLocal()
    user_repo = user_repo or get_user_repository()

    try:
        existing = await user_repo.get_by_username(session, username)
        if existing:
            logger.warning(f"Registration failed: username {username} already exists")
            raise AuthenticationError("Username already registered")

        hashed_pw = hash_password(password)
        user = await user_repo.create_user(session, username=username, hashed_password=hashed_pw, role="user")
        await session.commit()
        await session.refresh(user)

        token = create_access_token(user.id, user.username, user.role)
        logger.debug("Exiting register_user successfully")
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        }
    finally:
        if own_session:
            await session.close()

