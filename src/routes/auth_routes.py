import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.dtos.auth_dto import LoginRequestDTO, RegisterRequestDTO, TokenResponseDTO
from src.services.auth_service import authenticate_user, register_user
from src.repositories.user_repository import UserRepository, get_user_repository
from src.models.base import get_async_db
from src.utils.exceptions.auth import AuthenticationError

logger = logging.getLogger("triage_assistant.auth_routes")

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponseDTO, status_code=status.HTTP_200_OK)
async def login(
    payload: LoginRequestDTO,
    db: AsyncSession = Depends(get_async_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    logger.debug(f"Entering login route for username: {payload.username}")
    try:
        token_data = await authenticate_user(payload.username, payload.password, session=db, user_repo=user_repo)
        logger.debug("Exiting login route successfully")
        return TokenResponseDTO(**token_data)
    except AuthenticationError as exc:
        logger.warning(f"Login failed for username {payload.username}: {exc}")
        logger.debug("Exiting login route with HTTP 401")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc)
        )

@router.post("/register", response_model=TokenResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequestDTO,
    db: AsyncSession = Depends(get_async_db),
    user_repo: UserRepository = Depends(get_user_repository)
):
    logger.debug(f"Entering register route for username: {payload.username}")
    try:
        token_data = await register_user(payload.username, payload.password, session=db, user_repo=user_repo)
        logger.debug("Exiting register route successfully")
        return TokenResponseDTO(**token_data)
    except AuthenticationError as exc:
        logger.warning(f"Registration failed for username {payload.username}: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

